from flask import request, jsonify
import sqlalchemy as sa
from pydantic import ValidationError
from app import db
from app.main import bp
from app.models import Payment
from flask_login import login_required, current_user
from app.main.schema import NewPaymentSchema, EditStatusSchema
from flask_jwt_extended import jwt_required, get_jwt_identity



@bp.route('/payments', methods=["POST"])
@jwt_required()
def payment():
    try:
        data = NewPaymentSchema(**request.get_json())
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
            user_id= get_jwt_identity(), 
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
                "amount": float(payment.amount),
                "category": payment.category,
                "deadline": payment.deadline.isoformat(),
                "status": payment.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "fail",
            "message": "Failed to create payment"
        }), 500


@bp.route("/payments", methods=["GET"])
@jwt_required()
def get_payments():
    status = request.args.get('status')
    category = request.args.get('category')
    search = request.args.get('search') 
   
    sort_by = request.args.get('sort_by', 'deadline')  
    sort_order = request.args.get('sort_order', 'asc')  

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)

    try:
       
        orm_query = db.session.query(Payment).filter(Payment.user_id ==  get_jwt_identity()) # better than select
        
        if status:
            orm_query = orm_query.filter(Payment.status == status)
        if category:
            orm_query = orm_query.filter(Payment.category == category)
        if search:
            search_term = f"%{search}%"
            orm_query = orm_query.filter(
                sa.or_(
                    Payment.payment_name.ilike(search_term),
                    Payment.description.ilike(search_term)
                )
            )
        # Sorting
        sort_column = getattr(Payment, sort_by, Payment.deadline)
        if sort_order.lower() == 'desc':
            orm_query = orm_query.order_by(sort_column.desc())
        else:
            orm_query = orm_query.order_by(sort_column.asc())

        # Use db.paginate directly on the ORM query
        pagination = db.paginate(
            orm_query,
            page=page,
            per_page=per_page,
            error_out=False
        )

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
                    "status": status,
                    "category": category,
                    "search": search,
                    "sort_by": sort_by,
                    "sort_order": sort_order
                }
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "fail",
            "message": "Failed to fetch payments"
        }), 500
    
@bp.route('/payment/<int:payment_id>/status', methods=['PATCH'])
@jwt_required()
def change_status(payment_id):

    try:
      
        data = EditStatusSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({
            "status": "fail", 
            "errors": e.errors()
        }), 400
    except Exception:
        return jsonify({
            "status": "fail", 
            "message": "Invalid JSON"
        }), 400

    user_id = get_jwt_identity()

    
    payment = db.session.query(Payment).filter_by(id=payment_id, user_id=user_id).first()
    if not payment:
        return jsonify({
            "status": "fail",
            "message": "Payment not found or access denied"
        }), 404

    
    payment.status = data.status 
    db.session.commit()

    return jsonify({
        "status": "success",
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

    
@bp.route('/payments/<int:payment_id>', methods=["DELETE"])
@jwt_required()
def delete_payment(payment_id):
    user_id = get_jwt_identity()

 
    payment = db.session.query(Payment).filter_by(id=payment_id, user_id=user_id).first()

    if not payment:
        return jsonify({
            "status": "fail",
            "message": "Payment not found or access denied"
        }), 404

    try:
      
        db.session.delete(payment)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Payment {payment_id} deleted successfully"
        }), 200

    except Exception as e:
      
        return jsonify({
            "status": "fail",
            "message": "Failed to delete payment"
        }), 500