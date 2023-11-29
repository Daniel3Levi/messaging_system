from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Messagin System API",
        default_version="v1",
        description="RESTful API backend built with Django Rest Framework for handling messages between users."
                    " It provides a simple and efficient platform for users to send, receive, and manage messages.",
        terms_of_service="https://www.danielevi.co.il",
        contact=openapi.Contact(email="daniel@danielevi.co.il"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('messaging_app.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
