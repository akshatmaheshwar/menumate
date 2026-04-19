from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',views.home),
    path('dashboard/',views.dashboard),
    path('menu/',views.menu),
    path('order/',views.order),
    path('restaurant/',views.restaurant),
    path('api/signup/', views.handle_signup, name='handle_signup'),
    path('api/login/', views.handle_login, name='handle_login'),
    # Menu URLs
    path('menu/get_menus/', views.get_menus, name='get_menus'),
    path('menu/add_menu/', views.add_menu, name='add_menu'),
    path('menu/update_menu/', views.update_menu, name='update_menu'),
    path('menu/delete_menu/', views.delete_menu, name='delete_menu'),
    
    # Category URLs
    path('menu/get_categories/', views.get_categories, name='get_categories'),
    path('menu/add_category/', views.add_category, name='add_category'),
    path('menu/update_category/', views.update_category, name='update_category'),
    path('menu/delete_category/', views.delete_category, name='delete_category'),
    
    # Menu Item URLs
    path('menu/get_menu_items/', views.get_menu_items, name='get_menu_items'),
    path('menu/get_menu_item/', views.get_menu_item, name='get_menu_item'),
    path('menu/add_menu_item/', views.add_menu_item, name='add_menu_item'),
    path('menu/update_menu_item/', views.update_menu_item, name='update_menu_item'),
    path('menu/delete_menu_item/', views.delete_menu_item, name='delete_menu_item'),

    path('restaurant/restaurant_profile/', views.restaurant_profile, name='restaurant_profile'),

    path('order/<int:restaurant_id>/<int:table_number>/', views.order_page, name='order_page'),
    path('api/create_order/', views.create_order, name='create_order'),
    path('order/get_menu_items_as_guest/', views.get_menu_items_as_guest, name='get_menu_items_as_guest'),
    path('order/get_menus_as_guest/', views.get_menus_as_guest, name='get_menus_as_guest'),
    path('order/get_categories_as_guest/', views.get_categories_as_guest, name='get_categories_as_guest'),
    path('order/get_menu_items_as_guest/', views.get_menu_items_as_guest, name='get_menu_items_as_guest'),

    path('dashboard/api/get_restaurant_data/', views.get_restaurant_data, name='get_restaurant_data'),
    path('dashboard/api/update_order_status/', views.update_order_status, name='update_order_status'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)