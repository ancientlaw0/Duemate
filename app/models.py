import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    email: so.Mapped[str] = so.mapped_column(sa.String(200), index=True, unique=True, nullable=True)
    phone_number: so.Mapped[str] = so.mapped_column(sa.String(15), unique=True, nullable=True)
    payments: so.WriteOnlyMapped['Payment'] = so.relationship(back_populates='user')

    def __repr__(self):
        return f'<User {self.email or self.phone_number}>'


class Payment(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('user.id'), index=True)
    
    payment_name: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False)
    description: so.Mapped[str] = so.mapped_column(sa.String(300), nullable=True)

    amount: so.Mapped[float] = so.mapped_column(sa.Float(10, 2), nullable=False)
    category: so.Mapped[str] = so.mapped_column(
        sa.Enum("bills", "subscription", "loan", "tax", "other", name="category_enum"), 
        nullable=False)
    
    deadline: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=False) 
    status: so.Mapped[str] = so.mapped_column(
        sa.Enum("pending", "paid", "overdue", "cancelled", name="status_enum"), 
        nullable=False, default="pending" )
    
    user: so.Mapped[User] = so.relationship(back_populates='payments')

    def __repr__(self):
        return f'<Payment {self.payment_name}: {self.amount}>'