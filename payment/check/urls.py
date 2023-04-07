from rest_framework.schemas.coreapi import AutoSchema
from django.urls import path
from .views import Register, Login, WalletInfo, DepositFunds, VerifyDeposit, index
from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='API Documentation')

urlpatterns = [
    path('swagger-docs/', schema_view),
    path('register/', Register.as_view()),
    path('login/', Login.as_view()),
    path('wallet_info/', WalletInfo.as_view()),
    path('deposit/', DepositFunds.as_view()),
    path('deposit/verify/<str:reference>/', VerifyDeposit.as_view()),   
    path('index/', index.as_view())
]