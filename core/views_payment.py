import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Plan, UserProfile, PaymentHistory
import logging

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_checkout_session(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    
    # Determine the correct price ID based on the plan
    stripe_id = plan.stripe_price_id
            
    if not stripe_id:
        return JsonResponse({'error': f'O plano {plan.name} não possui um ID de preço do Stripe configurado.'}, status=400)

    # If the ID provided is a Product ID (starts with 'prod_'), fetch its default price
    price_id = stripe_id
    if stripe_id.startswith('prod_'):
        try:
            product = stripe.Product.retrieve(stripe_id)
            if not product.default_price:
                return JsonResponse({'error': f'O produto {stripe_id} não possui um preço padrão definido no Stripe. Defina um preço padrão no Dashboard.'}, status=400)
            price_id = product.default_price if isinstance(product.default_price, str) else product.default_price.id
        except Exception as e:
            return JsonResponse({'error': f'Erro ao buscar produto no Stripe: {str(e)}'}, status=400)

    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
            client_reference_id=request.user.id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=request.build_absolute_uri('/pagamento/sucesso/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/pagamento/cancelado/'),
            # Enable automatic tax calculation if needed
            # automatic_tax={'enabled': True},
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def payment_success(request):
    session_id = request.GET.get('session_id')
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                handle_checkout_session_completed(session)
        except Exception as e:
            logger.error(f"Error retrieving session in success view: {e}")
            
    return render(request, 'core/payment_success.html')

def payment_cancel(request):
    return render(request, 'core/payment_cancel.html')

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)

    return HttpResponse(status=200)

def handle_checkout_session_completed(session):
    client_reference_id = session.get('client_reference_id')
    stripe_customer_id = session.get('customer')
    
    # Retrieve the user
    try:
        user = User.objects.get(id=client_reference_id)
    except User.DoesNotExist:
        logger.error(f"User with ID {client_reference_id} not found.")
        return

    # Retrieve the subscription to get the plan/product
    subscription_id = session.get('subscription')
    if subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            price_data = subscription['items']['data'][0]['price']
            price_id = price_data['id']
            product_id = price_data.get('product')
            
            # Find the plan matching this price_id OR product_id
            # First check DB for exact price match
            plan = Plan.objects.filter(stripe_price_id=price_id).first()
            
            # If not found, check if we have a plan with the matching product ID
            if not plan and product_id:
                plan = Plan.objects.filter(stripe_price_id=product_id).first()
            
            # If still not found, check settings mapping (fallback)
            if not plan:
                if price_id == getattr(settings, 'STRIPE_PRICE_ID_APOIADOR', None):
                    plan = Plan.objects.filter(name__iexact='Apoiador').first()
                elif price_id == getattr(settings, 'STRIPE_PRICE_ID_IRRESTRITO', None):
                    plan = Plan.objects.filter(name__iexact='Irrestrito').first()
                elif price_id == getattr(settings, 'STRIPE_PRICE_ID_MECENAS', None):
                    plan = Plan.objects.filter(name__iexact='Mecenas').first()
            
            if plan:
                # Update user profile
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.current_plan = plan
                profile.stripe_subscription_id = subscription_id
                # Convert timestamp to datetime
                from datetime import datetime, timezone
                if 'current_period_end' in subscription:
                    profile.subscription_end_date = datetime.fromtimestamp(subscription['current_period_end'], tz=timezone.utc)
                profile.save()
                logger.info(f"Updated plan for user {user.username} to {plan.name}")
                
                # Record payment history
                amount_total = session.get('amount_total', 0) / 100.0  # Convert cents to currency unit
                
                # Check if payment history already exists for this session to avoid duplicates
                if not PaymentHistory.objects.filter(stripe_id=session.get('id')).exists():
                    PaymentHistory.objects.create(
                        user=user,
                        amount=amount_total,
                        status=session.get('payment_status', 'unknown'),
                        stripe_id=session.get('id'),
                        plan_name=plan.name
                    )
            else:
                logger.warning(f"Plan not found for price ID {price_id}")
                
        except Exception as e:
            logger.error(f"Error processing subscription: {e}")

@login_required
def cancel_subscription(request):
    if request.method == 'POST':
        try:
            profile = request.user.profile
            if profile.stripe_subscription_id:
                stripe.Subscription.modify(
                    profile.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                profile.cancel_at_period_end = True
                profile.save()
                return JsonResponse({'status': 'success', 'message': 'Assinatura cancelada com sucesso. Você terá acesso até o fim do período atual.'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Nenhuma assinatura ativa encontrada.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)
