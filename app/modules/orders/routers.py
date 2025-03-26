from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import SessionLocal
from app.modules.orders.models import (
    ShoppingCart, CartItem, Order, OrderItem, 
    Payment, Delivery, Feedback
)
from app.modules.orders.schemas import *

router = APIRouter(prefix="/orders", tags=["orders"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Shopping Cart CRUD ---

@router.post("/carts", response_model=ShoppingCartResponse, status_code=status.HTTP_201_CREATED)
def create_cart(user_id: int, db: Session = Depends(get_db)):
    existing_cart = db.query(ShoppingCart).filter(
        ShoppingCart.user_id == user_id,
        ShoppingCart.active == True
    ).first()
    
    if existing_cart:
        return existing_cart
    
    cart = ShoppingCart(user_id=user_id, active=True)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart

@router.get("/carts/user/{user_id}", response_model=ShoppingCartResponse)
def get_user_cart(user_id: int, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(
        ShoppingCart.user_id == user_id,
        ShoppingCart.active == True
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="No active shopping cart found for this user.")
    
    return cart

@router.get("/carts/{cart_id}", response_model=ShoppingCartResponse)
def get_cart(cart_id: int, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(ShoppingCart.id == cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found.")
    return cart

@router.delete("/carts/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cart(cart_id: int, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(
        ShoppingCart.id == cart_id,
        ShoppingCart.active == True
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found or already inactive.")
    
    cart.active = False
    db.commit()
    return None

# --- Cart Items CRUD ---

@router.post("/carts/{cart_id}/items", status_code=status.HTTP_201_CREATED)
def add_cart_item(cart_id: int, item_data: CartItemCreate, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(
        ShoppingCart.id == cart_id,
        ShoppingCart.active == True
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found or inactive.")
    
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart_id,
        CartItem.product_id == item_data.product_id
    ).first()
    
    if existing_item:
        existing_item.quantity += item_data.quantity
        db.commit()
        db.refresh(existing_item)
        return existing_item
    
    cart_item = CartItem(
        cart_id=cart_id,
        product_id=item_data.product_id,
        quantity=item_data.quantity
    )
    
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item

@router.get("/carts/{cart_id}/items")
def get_cart_items(cart_id: int, db: Session = Depends(get_db)):
    cart = db.query(ShoppingCart).filter(
        ShoppingCart.id == cart_id,
        ShoppingCart.active == True
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Shopping cart not found or inactive.")
    
    items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
    return items

@router.patch("/carts/items/{item_id}")
def update_cart_item(item_id: int, quantity: int, db: Session = Depends(get_db)):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")
    
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    
    cart = db.query(ShoppingCart).filter(
        ShoppingCart.id == item.cart_id,
        ShoppingCart.active == True
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Associated shopping cart is inactive.")
    
    item.quantity = quantity
    db.commit()
    db.refresh(item)
    return item

@router.delete("/carts/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    
    db.delete(item)
    db.commit()
    return None

# --- Order CRUD ---

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    order = Order(
        user_id=order_data.user_id,
        total_amount=order_data.total_amount,
        currency=order_data.currency,
        payment_method=order_data.payment_method,
        status="pending",
        active=True
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/", response_model=List[OrderResponse])
def get_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.active == True).offset(skip).limit(limit).all()
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order

@router.get("/user/{user_id}", response_model=List[OrderResponse])
def get_user_orders(user_id: int, db: Session = Depends(get_db)):
    orders = db.query(Order).filter(
        Order.user_id == user_id,
        Order.active == True
    ).all()
    return orders

@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int, 
    status: str = None, 
    payment_method: str = None,
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == order_id, Order.active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    if status is not None:
        valid_statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        order.status = status
    
    if payment_method is not None:
        valid_methods = ["qr", "paypal", "stripe"]
        if payment_method not in valid_methods:
            raise HTTPException(status_code=400, detail=f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")
        order.payment_method = payment_method
    
    db.commit()
    db.refresh(order)
    return order

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    
    order.active = False
    db.commit()
    return None

# --- Order Items CRUD ---

@router.post("/{order_id}/items", status_code=status.HTTP_201_CREATED)
def add_order_item(order_id: int, product_id: int, quantity: int, unit_price: float, db: Session = Depends(get_db)):
    # Verify order exists and is active
    order = db.query(Order).filter(Order.id == order_id, Order.active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    order_item = OrderItem(
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price
    )
    
    db.add(order_item)
    db.commit()
    db.refresh(order_item)
    return order_item

@router.get("/{order_id}/items")
def get_order_items(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.active == True).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    return items

# --- Payment CRUD ---

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payment_data: PaymentCreate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        Order.id == payment_data.order_id, 
        Order.active == True
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    existing_payment = db.query(Payment).filter(Payment.order_id == payment_data.order_id).first()
    if existing_payment:
        raise HTTPException(status_code=400, detail="Payment already exists for this order.")
    
    payment = Payment(
        order_id=payment_data.order_id,
        amount=payment_data.amount,
        method=payment_data.method,
        status="initiated"
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    order.status = "paid"
    db.commit()
    
    return payment

@router.get("/payments/order/{order_id}", response_model=PaymentResponse)
def get_order_payment(order_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found for this order.")
    return payment

@router.patch("/payments/{payment_id}", response_model=PaymentResponse)
def update_payment(payment_id: int, status: str, transaction_id: str = None, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")
    
    valid_statuses = ["initiated", "completed", "failed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    payment.status = status
    if transaction_id:
        payment.transaction_id = transaction_id
    
    db.commit()
    db.refresh(payment)
    return payment

# --- Delivery CRUD ---

@router.post("/deliveries", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
def create_delivery(delivery_data: DeliveryCreate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        Order.id == delivery_data.order_id, 
        Order.active == True
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    if order.status not in ["paid", "shipped"]:
        raise HTTPException(status_code=400, detail="Order must be paid before creating delivery.")
    
    existing_delivery = db.query(Delivery).filter(Delivery.order_id == delivery_data.order_id).first()
    if existing_delivery:
        raise HTTPException(status_code=400, detail="Delivery already exists for this order.")
    
    delivery = Delivery(
        order_id=delivery_data.order_id,
        delivery_address=delivery_data.delivery_address,
        delivery_status="pending",
        tracking_info=None,
        estimated_arrival=None
    )
    
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    
    if order.status == "paid":
        order.status = "shipped"
        db.commit()
    
    return delivery

@router.get("/deliveries/order/{order_id}", response_model=DeliveryResponse)
def get_order_delivery(order_id: int, db: Session = Depends(get_db)):
    delivery = db.query(Delivery).filter(Delivery.order_id == order_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found for this order.")
    return delivery

@router.patch("/deliveries/{delivery_id}", response_model=DeliveryResponse)
def update_delivery(
    delivery_id: int, 
    status: str = None, 
    tracking_info: str = None, 
    estimated_arrival: str = None,
    db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found.")
    
    if status is not None:
        valid_statuses = ["pending", "in_transit", "delivered", "cancelled"]
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        delivery.delivery_status = status
        
        if status == "delivered":
            order = db.query(Order).filter(Order.id == delivery.order_id).first()
            if order:
                order.status = "delivered"
                db.commit()
    
    if tracking_info is not None:
        delivery.tracking_info = tracking_info
    
    if estimated_arrival is not None:
        delivery.estimated_arrival = estimated_arrival
    
    db.commit()
    db.refresh(delivery)
    return delivery

# --- Feedback CRUD ---

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(feedback_data: FeedbackCreate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(
        Order.id == feedback_data.order_id, 
        Order.active == True
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or inactive.")
    
    if order.status != "delivered":
        raise HTTPException(status_code=400, detail="Feedback can only be left for delivered orders.")
    
    existing_feedback = db.query(Feedback).filter(
        Feedback.order_id == feedback_data.order_id, 
        Feedback.user_id == feedback_data.user_id
    ).first()
    
    if existing_feedback:
        raise HTTPException(status_code=400, detail="Feedback already exists for this order from this user.")
    
    if feedback_data.rating < 1 or feedback_data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
    
    feedback = Feedback(
        order_id=feedback_data.order_id,
        user_id=feedback_data.user_id,
        rating=feedback_data.rating,
        comment=feedback_data.comment
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback

@router.get("/feedback/order/{order_id}", response_model=List[FeedbackResponse])
def get_order_feedback(order_id: int, db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.order_id == order_id).all()
    return feedback

@router.get("/feedback/user/{user_id}", response_model=List[FeedbackResponse])
def get_user_feedback(user_id: int, db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.user_id == user_id).all()
    return feedback

@router.patch("/feedback/{feedback_id}", response_model=FeedbackResponse)
def update_feedback(
    feedback_id: int, 
    rating: int = None, 
    comment: str = None,
    db: Session = Depends(get_db)
):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found.")
    
    if rating is not None:
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")
        feedback.rating = rating
    
    if comment is not None:
        feedback.comment = comment
    
    db.commit()
    db.refresh(feedback)
    return feedback

@router.delete("/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(feedback_id: int, db: Session = Depends(get_db)):
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found.")
    
    db.delete(feedback)
    db.commit()
    return None