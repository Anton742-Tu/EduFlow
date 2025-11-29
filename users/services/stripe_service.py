from typing import Any, Dict, Optional

import stripe
from django.conf import settings

from materials.models import Course, Lesson

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """
    Сервис для работы с Stripe API
    """

    @staticmethod
    def create_product(name: str, description: str = "") -> Dict[str, Any]:
        """
        Создание продукта в Stripe
        """
        try:
            product = stripe.Product.create(
                name=name,
                description=description,
            )
            return product
        except stripe.error.StripeError as e:
            raise Exception(f"Ошибка создания продукта в Stripe: {str(e)}")

    @staticmethod
    def create_price(product_id: str, amount: int, currency: str = "usd") -> Dict[str, Any]:
        """
        Создание цены для продукта в Stripe
        """
        try:
            price = stripe.Price.create(
                product=product_id,
                unit_amount=amount * 100,  # Stripe работает в центах
                currency=currency,
            )
            return price
        except stripe.error.StripeError as e:
            raise Exception(f"Ошибка создания цены в Stripe: {str(e)}")

    @staticmethod
    def create_checkout_session(
        price_id: str, success_url: str, cancel_url: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Создание сессии для оплаты
        """
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
            )
            return session
        except stripe.error.StripeError as e:
            raise Exception(f"Ошибка создания сессии оплаты в Stripe: {str(e)}")

    @staticmethod
    def create_course_payment_session(course: Course, user_id: int) -> Dict[str, Any]:
        """
        Создание сессии оплаты для курса
        """
        # Создаем продукт в Stripe
        product = StripeService.create_product(name=course.title, description=course.description or "Оплата курса")

        # Создаем цену (предполагаем что курс имеет поле price)
        price = StripeService.create_price(
            product_id=product.id,
            amount=int(course.price) if hasattr(course, "price") else 1000,  # 10.00 USD по умолчанию
        )

        # Создаем сессию оплаты
        success_url = f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.FRONTEND_URL}/payment/cancel"

        metadata = {"course_id": str(course.id), "user_id": str(user_id), "type": "course"}

        session = StripeService.create_checkout_session(
            price_id=price.id, success_url=success_url, cancel_url=cancel_url, metadata=metadata
        )

        return {"session_id": session.id, "url": session.url, "product_id": product.id, "price_id": price.id}
