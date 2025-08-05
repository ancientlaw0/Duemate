from flask import request, jsonify
import sqlalchemy as sa
from pydantic import ValidationError
from app import db
from app.main import bp
from app.models import Payment
from flask_login import login_required, current_user
from app.main.schema import NewPaymentSchema, EditStatusSchema , PaymentFilterSchema
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import make_response

@bp.route('/payments', methods=["POST"])
@login_required
def payment():
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({
                "status": "fail", 
                "message": "No JSON data provided"
            }), 400
            
        data = NewPaymentSchema(**json_data)
        
    except ValidationError as e:
        return jsonify({
            "status": "fail", 
            "errors": e.errors()
        }), 400
    except Exception as e:
        return jsonify({
            "status": "fail", 
            "message": "Invalid JSON"
        }), 400

    try:
        payment = Payment(
            user_id=current_user.id,  # Use Flask-Login current_user
            payment_name=data.payment_name,
            description=data.description,
            amount=float(data.amount),
            category=data.category,
            deadline=data.deadline,
            status=data.status
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Payment created successfully",
            "payment": {
                "id": payment.id,
                "payment_name": payment.payment_name,
                "description": payment.description,  
                "amount": float(payment.amount),
                "category": payment.category,
                "deadline": payment.deadline.isoformat(),
                "status": payment.status,
                "user_id": payment.user_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {str(e)}")  
        return jsonify({
            "status": "fail",
            "message": f"Failed to create payment: {str(e)}"  
        }), 500

    
@bp.route("/payments", methods=["GET"])
# @jwt_required()  # JWT is commented out for now
def get_payments():
    try:
        filter_data = PaymentFilterSchema(
            status=request.args.get('status'),
            category=request.args.get('category'),
            search=request.args.get('search'),
            sort_by=request.args.get('sort_by', 'deadline'),
            sort_order=request.args.get('sort_order', 'asc'),
            page=int(request.args.get("page", 1)),
            per_page=min(int(request.args.get("per_page", 10)), 100)
        )
    except ValidationError as e:
        return jsonify({
            "status": "fail",
            "errors": e.errors()
        }), 400
    except (ValueError, TypeError):
        return jsonify({
            "status": "fail",
            "message": "Invalid query parameters"
        }), 400

    # user_id = get_jwt_identity()  # JWT removed, no filtering by user now

    try:
        orm_query = db.session.query(Payment)  # No user filtering

        # Apply filters if provided
        if filter_data.status:
            orm_query = orm_query.filter(Payment.status == filter_data.status)
        if filter_data.category:
            orm_query = orm_query.filter(Payment.category == filter_data.category)
        if filter_data.search:
            search_term = f"%{filter_data.search}%"
            orm_query = orm_query.filter(
                sa.or_(
                    Payment.payment_name.ilike(search_term),
                    Payment.description.ilike(search_term)
                )
            )

        # Sorting
        sort_column = getattr(Payment, filter_data.sort_by, Payment.deadline)
        if filter_data.sort_order == 'desc':
            orm_query = orm_query.order_by(sort_column.desc())
        else:
            orm_query = orm_query.order_by(sort_column.asc())

        # Pagination
        pagination = db.paginate(
            orm_query,
            page=filter_data.page,
            per_page=filter_data.per_page,
            error_out=False
        )

        # Response JSON
        return jsonify({
            "status": "success",
            "data": {
                "payments": [
                    {
                        "id": payment.id,
                        "payment_name": payment.payment_name,
                        "description": payment.description,
                        "amount": float(payment.amount),
                        "category": payment.category,
                        "deadline": payment.deadline.isoformat(),
                        "status": payment.status
                    }
                    for payment in pagination.items
                ],
                "pagination": {
                    "page": pagination.page,
                    "per_page": pagination.per_page,
                    "total_count": pagination.total,
                    "total_pages": pagination.pages,
                    "has_next": pagination.has_next,
                    "has_prev": pagination.has_prev,
                    "next_page": pagination.next_num if pagination.has_next else None,
                    "prev_page": pagination.prev_num if pagination.has_prev else None
                },
                "filters": {
                    "status": filter_data.status,
                    "category": filter_data.category,
                    "search": filter_data.search,
                    "sort_by": filter_data.sort_by,
                    "sort_order": filter_data.sort_order
                }
            }
        }), 200

    except Exception as e:
        print("Database error:", str(e))
        return jsonify({
            "status": "fail",
            "message": "Failed to fetch payments"
        }), 500

    

@bp.route('/payment/<int:payment_id>/status', methods=['PATCH'])
# @jwt_required()
def change_status(payment_id):
    try:
        json_data = request.get_json()
        
    
        if not json_data:
            return jsonify({
                "status": "fail", 
                "message": "No JSON data provided"
            }), 400
            
        data = EditStatusSchema(**json_data)
        
    except ValidationError as e:
        return jsonify({
            "status": "fail", 
            "errors": e.errors()
        }), 400
    except Exception as e:
        return jsonify({
            "status": "fail", 
            "message": "Invalid JSON"
        }), 400

    try:

        payment = db.session.query(Payment).filter_by(id=payment_id).first()

        if not payment:
            return jsonify({
                "status": "fail",
                "message": "Payment not found"  
            }), 404

     
        old_status = payment.status
        
      
        if old_status == data.status:
            return jsonify({
                "status": "success",
                "message": f"Payment status is already '{data.status}'",
                "data": {
                    "id": payment.id,
                    "payment_name": payment.payment_name,
                    "description": payment.description,
                    "amount": float(payment.amount),
                    "category": payment.category,
                    "deadline": payment.deadline.isoformat(),
                    "status": payment.status
                }
            }), 200
        
       
        payment.status = data.status 
        
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Payment status updated successfully",
            "data": {
                "id": payment.id,
                "payment_name": payment.payment_name,
                "description": payment.description,
                "amount": float(payment.amount),
                "category": payment.category,
                "deadline": payment.deadline.isoformat(),
                "status": payment.status,
                "previous_status": old_status  
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()  
        print(f"Database error updating payment {payment_id}: {str(e)}")
        return jsonify({
            "status": "fail",
            "message": f"Failed to update payment status: {str(e)}"
        }), 500
    

@bp.route('/payments/<int:payment_id>', methods=["DELETE"])
# @jwt_required() 
def delete_payment(payment_id):
    try:
      
        payment = db.session.query(Payment).filter_by(id=payment_id).first()

        if not payment:
            return jsonify({
                "status": "fail",
                "message": "Payment not found" 
            }), 404

       
        payment_name = payment.payment_name
        payment_amount = float(payment.amount)
        
      
        db.session.delete(payment)
        db.session.commit()
        
        print(f"Payment {payment_id} ('{payment_name}') deleted successfully")  

        return jsonify({
            "status": "success",
            "message": f"Payment '{payment_name}' deleted successfully",
            "deleted_payment": {
                "id": payment_id,
                "payment_name": payment_name,
                "amount": payment_amount
            }
        }), 200

    except Exception as e:
        db.session.rollback() 
        print(f"Database error deleting payment {payment_id}: {str(e)}") 
        return jsonify({
            "status": "fail",
            "message": f"Failed to delete payment: {str(e)}"  
        }), 500