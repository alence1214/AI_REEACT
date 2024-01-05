from decouple import config
import stripe
import requests
import os
import datetime

import app.promo_code.schema as promocodeSchema

stripe.api_key = config("STRIPE_SECRET")

class StripeManager:
    async def create_customer(customer_data):
        try:
            new_customer = stripe.Customer.create(
                name=customer_data["full_name"],
                email=customer_data["email"],
                phone=customer_data["phone"],
                address={
                    "city": customer_data["province"],
                    "country": customer_data["pays"],
                    "postal_code": customer_data["postal_code"]
                }
            )
            return new_customer
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return None
        
    async def delete_customer(customer_id: str):
        try:
            deleted_customer = stripe.Customer.delete(customer_id)
            return deleted_customer
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e.code

    async def create_subscription(customer_id: str, plan_id: str):
        try:
            new_subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[
                    {
                        "plan": plan_id
                    }
                ]
            )
            return new_subscription
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e.code

    async def update_subscription(subscription_id: str, plan_id: str):
        try:
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[
                    {
                        "id": subscription_id,
                        "plan": plan_id
                    }
                ]
            )
            return updated_subscription
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e.code

    async def cancel_subscription(subscription_id: str):
        try:
            canceled_subscription = stripe.Subscription.delete(subscription_id)
            return canceled_subscription
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
    
    async def create_payment_method(payment_method_data):
        try:
            new_payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": payment_method_data["card_number"],
                    "exp_month": payment_method_data["expiration_date"].strip("/")[0],
                    "exp_year": payment_method_data["expiration_date"].strip("/")[1],
                    "cvc": payment_method_data["cvc"]
                }
            )
            return new_payment_method
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e.code
        
    async def create_payment_intent(customer_id: str, amount: int):
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount * 100,
                currency="EUR",
                customer=customer_id
            )
            return payment_intent.stripe_id
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e.code
    
    async def create_invoice(customer_id: str, amount: int, description: str):
        
        try:
            new_invoice = stripe.Invoice.create(
                customer=customer_id
            )
            new_invoice_item = stripe.InvoiceItem.create(
                customer=customer_id,
                invoice=new_invoice.stripe_id,
                amount=int(amount*100),
                currency="eur",
                description=description
            )
            new_invoice.finalize_invoice()
            return new_invoice.stripe_id
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return None
    
    async def create_intent_checkout_session(paymentintent_id: str):
        try:
            session = stripe.checkout.Session.create(
                payment_intent_data={
                    "payment_intent": paymentintent_id
                },
                mode="payment",
                success_url="localhost:3000//confirmation",
                cancel_url="localhost:3000://cancel"
            )
            return session.stripe_id
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e.code
        
    async def create_promo_code(promo_data: dict):
        try:
            start_at = datetime.datetime.strptime(promo_data["start_at"], "%Y-%m-%d %H:%M:%S")
            end_at = datetime.datetime.strptime(promo_data["end_at"], "%Y-%m-%d %H:%M:%S")
            
            # Calculate the month difference
            month_diff = (end_at.year - start_at.year) * 12 + (end_at.month - start_at.month)
            new_coupon = stripe.Coupon.create(
                percent_off=promo_data["amount"] if not promo_data["method"] else None,
                amount_off=int(promo_data["amount"] * 100) if promo_data["method"] else None,
                currency="eur" if promo_data["method"] else None,
                duration="repeating",
                duration_in_months=month_diff
            )
            new_promo_code = stripe.PromotionCode.create(
                code=promo_data["code_title"].replace(' ', '') if len(promo_data["code_title"]) != 0 else None,
                coupon=new_coupon.stripe_id,
                expires_at=int(end_at.timestamp())
            )
            return new_promo_code
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return None
    
    async def get_subscription_start_date(subscription_id: str):
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            start_date = subscription.current_period_start
            start_date = datetime.datetime.fromtimestamp(start_date)
            start_date = start_date.strftime("%y-%m-%d %H:%M:%S")
            return start_date
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e.code
        
    async def get_card_data_by_id(card_id: str):
        try:
            card_info = stripe.PaymentMethod.retrieve(card_id)
            card_detail = {
                "payment_method_id": card_id,
                "card_number": card_info["card"]["last4"],
                "card_holdername": '',
                "cvc": "***",
                "expiration_date": f'{card_info["card"]["exp_month"]}/{card_info["card"]["exp_year"]}'
            }
            return card_detail
        except Exception as e:
            print("StripeManger Exception:", e)
            return None
    
    async def set_default_payment_method(customer_id, payment_method_id):
        try:
            customer = stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    "default_payment_method": payment_method_id
                }
            )
            return customer
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e._message
        
    async def link_payment_method_to_customer(customer_id, payment_method_id):
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            return payment_method
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e._message)
            return e.code
    
    async def link_test_card_to_customer(customer_id):
        try:
            payment_method = stripe.PaymentMethod.attach(
                "pm_card_visa",
                customer=customer_id
            )
            return payment_method
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e.code
        
    async def pay_for_monthly_usage(customer_id, promo_code):
        try:
            coupon_id = None
            if promo_code:
                promotion_code = stripe.PromotionCode.retrieve(promo_code)
                coupon_id = promotion_code.coupon.id
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[
                    {
                        "price": config("SIGN_UP_PRICE_ID")
                    }
                ],
                payment_settings={
                    'payment_method_types': ['card']
                },
                coupon=coupon_id if coupon_id else None,
                expand=["latest_invoice.payment_intent"]
            )
            return subscription
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e._message
        
    async def unsubscribe(subsctiption_id: str):
        try:
            subsctiption = stripe.Subscription.retrieve(subsctiption_id)
            subsctiption.delete()
            return True
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return False
    
    async def pay_for_new_keywordurl(customer_id: str):
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[
                    {
                        "price": config("NEW_KEYWORD_URL_PRICE_ID")
                    }
                ],
                payment_settings={
                    'payment_method_types': ['card']
                },
                expand=["latest_invoice.payment_intent"]
            )
            return subscription
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e._message
        
    async def pay_for_invoice(invoice_id: str):
        try:
            result = stripe.Invoice.pay(invoice_id)
            return result
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            print(e.code, e._message)
            return e._message
        
    async def create_invoice_data_from_invoice_id(invoice_id: str, user_id):
        try:
            invoice = stripe.Invoice.retrieve(invoice_id)
            invoice_detail = []
            
            for data in invoice.lines.data:
                product_id = data.price.product
                product = stripe.Product.retrieve(product_id)
                
                product_name = product.name
                price = data.price.unit_amount / 100
                quantity = data.quantity
                
                invoice_detail.append(
                    {
                        "service_name": product_name,
                        "price": price,
                        "count": quantity
                    }
                )
            
            currency = invoice.currency
            
            payment_intent = stripe.PaymentIntent.retrieve(invoice.payment_intent)
            payment_method_id = payment_intent.payment_method
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            payment_method_type = payment_method.type
            
            invoice_pdf_url = invoice.invoice_pdf
            response = requests.get(invoice_pdf_url)
            os.makedirs("static/invoices", exist_ok=True)
            pdf_url = f"static/invoices/invoice_{invoice_id}.pdf"
            if response.status_code == 200:
                with open(pdf_url, 'wb') as file:
                    file.write(response.content)
                print(f"{pdf_url} Downloaded!")
            else:
                pdf_url = ""
                print("Failed to download PDF.")
            
            invoice_data = {
                "service_detail": product_name,
                "invoice_detail": {
                    "invoice_detail": invoice_detail,
                    "currency": currency
                },
                "payment_method": payment_method_type,
                "bill_from": -1,
                "bill_to": user_id,
                "status": "On Hold",
                "total_amount": str(invoice.total/100),
                "stripe_id": invoice_id,
                "pdf_url": pdf_url
            }
            return invoice_data
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return None
        
    async def create_invoice_data_from_subscription_id(subscription_id: str, customer_id):
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            latest_invoice_id = subscription.latest_invoice
            invoice = stripe.Invoice.retrieve(latest_invoice_id)
            invoice_detail = []
            
            if invoice.status != 'paid':
                if invoice.payment_intent != None:
                    payment_intent = stripe.PaymentIntent.retrieve(invoice.payment_intent)
                    if payment_intent.last_payment_error != None:
                        print(payment_intent.last_payment_error.message)
                        return payment_intent.last_payment_error.code
                return "Paiement échoué"
            
            for data in invoice.lines.data:
                product_id = data.price.product
                product = stripe.Product.retrieve(product_id)
                
                product_name = product.name
                price = data.price.unit_amount / 100
                quantity = data.quantity
                
                invoice_detail.append(
                    {
                        "service_name": product_name,
                        "price": price,
                        "count": quantity
                    }
                )
            
            promo_code = None
            if subscription.discount:
                promo_code = dict()
                coupon_id = subscription.discount.coupon.id
                coupon = stripe.Coupon.retrieve(coupon_id)
                discount_amount = coupon["amount_off"] if coupon["amount_off"] != None else coupon["percent_off"]
                coupon_type = "percentage" if coupon["amount_off"] == None else coupon["currency"]
                promo_code["coupon_code"] = coupon_id
                promo_code["discount_amount"] =  discount_amount
                promo_code["coupon_type"] = coupon_type
            
            currency = invoice.currency
            
            invoice_pdf_url = invoice.invoice_pdf
            response = requests.get(invoice_pdf_url)
            os.makedirs("static/invoices", exist_ok=True)
            pdf_url = f"static/invoices/invoice_{latest_invoice_id}.pdf"
            if response.status_code == 200:
                with open(pdf_url, 'wb') as file:
                    file.write(response.content)
                print(f"{pdf_url} Downloaded!")
            else:
                pdf_url = ""
                print("Failed to download PDF.")
            
            invoice_data = {
                "service_detail": product_name,
                "invoice_detail": {
                    "invoice_detail": invoice_detail,
                    "currency": currency,
                    "promo_apply": promo_code,
                },
                "payment_method": "Card",
                "bill_from": -1,
                "bill_to": customer_id,
                "status": "Completed",
                "total_amount": str(invoice.total/100),
                "stripe_id": latest_invoice_id,
                "pdf_url": pdf_url
            }
            return invoice_data
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return e.code
    
    async def get_cus_id_from_sub_id(subscription_id: str):
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            customer_id = subscription.customer
            return customer_id
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return None
    
    async def check_promo_code(promo_code_id: str):
        promo = stripe.PromotionCode.retrieve(promo_code_id)
        if promo.coupon.valid:
            return True
        else:
            return False
        
    async def apply_promo_subscription(promo_code_id, subscription_id):
        try:
            promo_code = stripe.PromotionCode.retrieve(promo_code_id)
            coupon_id = promo_code.coupon.id
            subscription = stripe.Subscription.modify(
                subscription_id,
                coupon=coupon_id
            )
            return True
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return False
        
    async def delete_promocode(promo_stripe_id: str):
        try:
            promo_code = stripe.PromotionCode.retrieve(promo_stripe_id)
            coupon_id = promo_code.coupon.id
            print(promo_stripe_id, coupon_id)
            stripe.Coupon.delete(coupon_id)
            return True
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return False
        
    async def delete_payment_method(card_stripe_id: str):
        try:
            stripe.PaymentMethod.detach(card_stripe_id)
            return True
        except stripe.error.StripeError as e:
            print("StripeManger Exception:", e)
            return False
    
    async def check_subscription(subscription_id: str=None):
        try:
            if subscription_id == None:
                return False
            subscription = stripe.Subscription.retrieve(subscription_id)
            if subscription.status == "active":
                return True
            return False
        except stripe.error.StripeError as e:
            print("Stripe check_subscription:", e)
            return False