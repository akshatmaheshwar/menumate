from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from .models import Restaurant, Menu, Category, MenuItem, Order, OrderItem
from django.contrib.auth.decorators import login_required
import json
import uuid
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

def get_restaurant_data(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        restaurant = request.user.restaurant
        if not restaurant:
            return JsonResponse({'error': 'User is not associated with a restaurant'}, status=400)
        
        # Get all processing orders with their items
        orders = Order.objects.filter(
            restaurant=restaurant,
            status__in=['received', 'processing', 'completed']
        ).order_by('-created_at')
        
        orders_data = []
        for order in orders:
            order_items = OrderItem.objects.filter(order=order).select_related('menu_item')
            items_data = [{
                'id': item.menu_item.id,
                'name': item.menu_item.name,
                'description': item.menu_item.description,
                'price': float(item.menu_item.price),
                'quantity': item.quantity,
                'image': item.menu_item.image.url if item.menu_item.image else None
            } for item in order_items]
            
            orders_data.append({
                'id': order.id,
                'table_number': order.table_number,
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'items': items_data
            })
        
        return JsonResponse({
            'restaurant': {
                'id': restaurant.id,
                'name': restaurant.name,
                'number_of_tables': restaurant.number_of_tables
            },
            'orders': orders_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_order_status(request):
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        new_status = data.get('status')
        
        if not order_id or not new_status:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
            
        order = get_object_or_404(Order, id=order_id)
        
        # Validate status transition
        valid_transitions = {
            'received': ['processing', 'completed'],
            'processing': ['completed'],
            'completed': []  # Can't change from completed
        }
        
        if new_status not in valid_transitions.get(order.status, []):
            return JsonResponse({
                'error': f'Invalid status transition from {order.status} to {new_status}'
            }, status=400)
        
        order.status = new_status
        order.save()
        
        return JsonResponse({
            'success': True,
            'new_status': new_status,
            'order_id': order_id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_order(request):
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if not all(field in data for field in ['restaurant_id', 'table_number', 'items']):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Create order
        order = Order.objects.create(
            restaurant_id=data['restaurant_id'],
            table_number=data['table_number'],
            status='received'
        )
        
        # Add order items
        for item in data['items']:
            menu_item = get_object_or_404(MenuItem, id=item['item_id'])
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=item.get('quantity', 1)
            )
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'message': 'Order placed successfully'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def order_page(request, restaurant_id, table_number):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    menus = Menu.objects.filter(restaurant=restaurant)
    
    # Get the first menu by default (you might want to add menu selection logic)
    active_menu = menus.first()
    categories = Category.objects.filter(menu=active_menu) if active_menu else []
    
    context = {
        'restaurant': restaurant,
        'table_number': table_number,
        'menus': menus,
        'categories': categories,
        'active_menu_id': active_menu.id if active_menu else None,
    }
    return render(request, 'order.html', context)

@csrf_exempt
def get_menus_as_guest(request):
    restaurant_id = request.GET.get('restaurant_id')
    if not restaurant_id:
        return JsonResponse({'error': 'Restaurant ID is required'}, status=400)
    
    menus = Menu.objects.filter(restaurant_id=restaurant_id).values('id', 'name')
    return JsonResponse({'menus': list(menus)})
@csrf_exempt
def get_categories_as_guest(request):
    restaurant_id = request.GET.get('restaurant_id')
    menu_id = request.GET.get('menu_id')
    
    if not restaurant_id:
        return JsonResponse({'error': 'Restaurant ID is required'}, status=400)
    
    categories = Category.objects.filter(menu__restaurant_id=restaurant_id)
    
    if menu_id and menu_id != 'all':
        categories = categories.filter(menu_id=menu_id)
    
    categories = categories.values('id', 'name', 'menu_id')
    return JsonResponse({'categories': list(categories)})
@csrf_exempt
def get_menu_items_as_guest(request):
    restaurant_id = request.GET.get('restaurant_id')
    menu_id = request.GET.get('menu_id', 'all')
    category_id = request.GET.get('category_id', 'all')
    
    if not restaurant_id:
        return JsonResponse({'error': 'Restaurant ID is required'}, status=400)
    
    menu_items = MenuItem.objects.filter(category__menu__restaurant_id=restaurant_id)
    
    if menu_id and menu_id != 'all':
        menu_items = menu_items.filter(category__menu_id=menu_id)
    
    if category_id and category_id != 'all':
        menu_items = menu_items.filter(category_id=category_id)
    
    menu_items = menu_items.values(
        'id', 'name', 'description', 'price', 'image', 
        'category_id', 'category__name'
    )
    items_list = list(menu_items)
    for item in items_list:
        if item['image']:
            item['image'] = request.build_absolute_uri(item['image'])
    
    return JsonResponse({'menu_items': items_list})
    

@login_required
@require_http_methods(["GET", "POST"])
def restaurant_profile(request):
    if not request.user.restaurant:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'No restaurant associated with this account'}, status=400)
        return redirect('home')
    
    restaurant = request.user.restaurant
    
    if request.method == 'POST':
        try:
            # For POST requests, use request.POST for form data or request.body for JSON
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
                
            restaurant.name = data.get('name', restaurant.name)
            restaurant.description = data.get('description', restaurant.description)
            restaurant.contact_email = data.get('contact_email', restaurant.contact_email)
            restaurant.contact_phone = data.get('contact_phone', restaurant.contact_phone)
            restaurant.address = data.get('address', restaurant.address)
            restaurant.number_of_tables = data.get('number_of_tables', restaurant.number_of_tables)
            restaurant.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    data = {
        'id': restaurant.id,
        'name': restaurant.name,
        'description': restaurant.description,
        'contact_email': restaurant.contact_email,
        'contact_phone': restaurant.contact_phone,
        'address': restaurant.address,
        'number_of_tables': restaurant.number_of_tables
    }
    return JsonResponse(data)

@login_required
def get_menus(request):
    restaurant = request.user.restaurant
    if not restaurant:
        return JsonResponse({'error': 'No restaurant found'}, status=400)
    
    menu_id = request.GET.get('menu_id')  # Get the menu_id from query params
    if menu_id:
        # Return only the requested menu
        menu = get_object_or_404(Menu, id=menu_id, restaurant=restaurant)
        return JsonResponse({'menu': {'id': menu.id, 'name': menu.name}})
    else:
        # Return all menus (if no ID is provided)
        menus = Menu.objects.filter(restaurant=restaurant)
        data = {'menus': [{'id': menu.id, 'name': menu.name} for menu in menus]}
        return JsonResponse(data)

@login_required
def get_categories(request):
    restaurant = request.user.restaurant
    if not restaurant:
        return JsonResponse({'error': 'No restaurant found'}, status=400)
    
    menu_id = request.GET.get('menu_id')
    if menu_id:
        categories = Category.objects.filter(menu__restaurant=restaurant, menu_id=menu_id)
    else:
        categories = Category.objects.filter(menu__restaurant=restaurant)
    
    data = {
        'categories': [{
            'id': cat.id, 
            'name': cat.name,
            'menu_name': cat.menu.name
        } for cat in categories]
    }
    return JsonResponse(data)

@login_required
def get_menu_items(request):
    restaurant = request.user.restaurant
    if not restaurant:
        return JsonResponse({'error': 'No restaurant found'}, status=400)
    
    menu_id = request.GET.get('menu_id')
    category_id = request.GET.get('category_id')
    
    items = MenuItem.objects.filter(category__menu__restaurant=restaurant)
    
    if menu_id:
        items = items.filter(category__menu_id=menu_id)
    if category_id and category_id != 'all':
        items = items.filter(category_id=category_id)
    
    data = {
        'menu_items': [{
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': str(item.price),
            'image': item.image.url if item.image else None,
            'category_name': item.category.name
        } for item in items]
    }
    return JsonResponse(data)

@login_required
def get_menu_item(request):
    restaurant = request.user.restaurant
    if not restaurant:
        return JsonResponse({'error': 'No restaurant found'}, status=400)
    
    item_id = request.GET.get('item_id')
    if not item_id:
        return JsonResponse({'error': 'Item ID is required'}, status=400)
    
    item = get_object_or_404(MenuItem, id=item_id, category__menu__restaurant=restaurant)
    
    data = {
        'menu_item': {
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': str(item.price),
            'category_id': item.category.id
        }
    }
    return JsonResponse(data)

@login_required
def add_menu(request):
    if request.method == 'POST':
        try:
            restaurant = request.user.restaurant
            if not restaurant:
                return JsonResponse({'error': 'No restaurant found'}, status=400)
            
            name = request.POST.get('name')
            if not name:
                return JsonResponse({'error': 'Menu name is required'}, status=400)
            
            menu = Menu.objects.create(
                name=name,
                restaurant=restaurant
            )
            
            return JsonResponse({'success': True, 'menu_id': menu.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def update_menu(request):
    if request.method == 'POST':
        try:
            restaurant = request.user.restaurant
            if not restaurant:
                return JsonResponse({'error': 'No restaurant found'}, status=400)
            
            menu_id = request.POST.get('id')
            name = request.POST.get('name')
            
            if not all([menu_id, name]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            menu = get_object_or_404(Menu, id=menu_id, restaurant=restaurant)
            menu.name = name
            menu.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def delete_menu(request):
    if request.method == 'POST':
        try:
            restaurant = request.user.restaurant
            if not restaurant:
                return JsonResponse({'error': 'No restaurant found'}, status=400)
            
            data = json.loads(request.body)
            menu_id = data.get('id')
            
            if not menu_id:
                return JsonResponse({'error': 'Menu ID is required'}, status=400)
            
            menu = get_object_or_404(Menu, id=menu_id, restaurant=restaurant)
            menu.delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def add_category(request):
    if request.method == 'POST':
        try:
            restaurant = request.user.restaurant
            if not restaurant:
                return JsonResponse({'error': 'No restaurant found'}, status=400)
            
            menu_id = request.POST.get('menu_id')
            name = request.POST.get('name')
            
            if not all([menu_id, name]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            menu = get_object_or_404(Menu, id=menu_id, restaurant=restaurant)
            category = Category.objects.create(
                name=name,
                menu=menu
            )
            
            return JsonResponse({'success': True, 'category_id': category.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def update_category(request):
    if request.method == 'POST':
        try:
            restaurant = request.user.restaurant
            if not restaurant:
                return JsonResponse({'error': 'No restaurant found'}, status=400)
            
            category_id = request.POST.get('id')
            menu_id = request.POST.get('menu_id')
            name = request.POST.get('name')
            
            if not all([category_id, menu_id, name]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            category = get_object_or_404(Category, id=category_id, menu__restaurant=restaurant)
            menu = get_object_or_404(Menu, id=menu_id, restaurant=restaurant)
            
            category.name = name
            category.menu = menu
            category.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def delete_category(request):
    if request.method == 'POST':
        try:
            restaurant = request.user.restaurant
            if not restaurant:
                return JsonResponse({'error': 'No restaurant found'}, status=400)
            
            data = json.loads(request.body)
            category_id = data.get('id')
            
            if not category_id:
                return JsonResponse({'error': 'Category ID is required'}, status=400)
            
            category = get_object_or_404(Category, id=category_id, menu__restaurant=restaurant)
            category.delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def add_menu_item(request):
    if request.method == 'POST':
        try:
            restaurant = request.user.restaurant
            if not restaurant:
                return JsonResponse({'error': 'No restaurant found'}, status=400)
            
            category_id = request.POST.get('category_id')
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            price = request.POST.get('price')
            
            if not all([category_id, name, price]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            category = get_object_or_404(Category, id=category_id, menu__restaurant=restaurant)
            
            menu_item = MenuItem(
                category=category,
                name=name,
                description=description,
                price=price
            )
            
            if 'image' in request.FILES:
                menu_item.image = request.FILES['image']
            
            menu_item.save()
            
            return JsonResponse({'success': True, 'item_id': menu_item.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def update_menu_item(request):
    if request.method == 'POST':
        try:
            restaurant = request.user.restaurant
            if not restaurant:
                return JsonResponse({'error': 'No restaurant found'}, status=400)
            
            item_id = request.POST.get('id')
            category_id = request.POST.get('category_id')
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            price = request.POST.get('price')
            
            if not all([item_id, category_id, name, price]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            menu_item = get_object_or_404(MenuItem, id=item_id, category__menu__restaurant=restaurant)
            category = get_object_or_404(Category, id=category_id, menu__restaurant=restaurant)
            
            menu_item.category = category
            menu_item.name = name
            menu_item.description = description
            menu_item.price = price
            
            if 'image' in request.FILES:
                menu_item.image = request.FILES['image']
            
            menu_item.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def delete_menu_item(request):
    if request.method == 'POST':
        try:
            restaurant = request.user.restaurant
            if not restaurant:
                return JsonResponse({'error': 'No restaurant found'}, status=400)
            
            data = json.loads(request.body)
            item_id = data.get('id')
            
            if not item_id:
                return JsonResponse({'error': 'Item ID is required'}, status=400)
            
            menu_item = get_object_or_404(MenuItem, id=item_id, category__menu__restaurant=restaurant)
            menu_item.delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

User = get_user_model()

def handle_signup(request):
    if request.method == 'POST':
        # Get form data
        email = request.POST.get('signup-email')
        password = request.POST.get('signup-password')
        confirm_password = request.POST.get('reentered_signup-password')
        restaurant_name = request.POST.get('restaurant-name')
        description = request.POST.get('restaurant-description')
        tables = request.POST.get('restaurant-tables')
        phone = request.POST.get('contact-phone')
        address = request.POST.get('contact-address')

        # Basic validation
        if not email or '@' not in email:
            return JsonResponse({'success': False, 'error': 'Invalid email'})
        if not password or len(password) < 6:
            return JsonResponse({'success': False, 'error': 'Password must be at least 6 characters'})
        if password != confirm_password:
            return JsonResponse({'success': False, 'error': 'Passwords do not match'})
        if not restaurant_name:
            return JsonResponse({'success': False, 'error': 'Restaurant name is required'})
        if not tables or not tables.isdigit() or int(tables) <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid number of tables'})

        try:
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

            # Create restaurant
            restaurant = Restaurant.objects.create(
                name=restaurant_name,
                description=description,
                number_of_tables=int(tables),
                contact_phone=phone,
                contact_email=email,
                address=address,
            )

            # Associate user with restaurant
            user.restaurant = restaurant
            user.save()

            # Log the user in
            login(request, user)

            return JsonResponse({'success': True, 'redirect': '/tabletapapp/dashboard/'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def handle_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return JsonResponse({'success': True, 'redirect': '/tabletapapp/dashboard/'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid credentials'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def home(request):
    return render(request,'home.html')

def dashboard(request):
    return render(request,'dashboard.html')

def menu(request):
    return render(request,'menu.html')

def order(request):
    return render(request,'order.html')

def restaurant(request):
    return render(request,'restaurant.html')

