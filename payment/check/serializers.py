from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from  .models import Wallet, WalletTransaction
from django.conf import settings
import requests
from django.db.models import Sum


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer to validate and create a new user
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}    
        }

    def create(self, validated_data):
        password = validated_data['password']
        user = User(
            username=validated_data['username'],
            email=validated_data['email']
        )
        
        user.set_password(password)
        user.save()
        
        Token.objects.create(user=user)
        return user
    
class WalletSerializer(serializers.ModelSerializer):
    """
    Serializers to validate the user's wallet 
    """
    balance = serializers.SerializerMethodField()

    def get_balance(self, obj):
        bal = WalletTransaction.objects.filter(
            wallet=obj, status="success").aggregate(Sum('amount'))['amount__sum']
        return bal

    class Meta:
        model = Wallet
        fields = ['id', 'currency', 'balance']


def is_amount(value):
    if value <= 0:
        raise serializers.ValidationError({"detail": "Invalid Amount"})
    return value    

class DepositSerializer(serializers.Serializer):
    amount = serializers.IntegerField(validators=[is_amount])
    email = serializers.EmailField()

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            return value
        raise serializers.ValidationError({"detail": "Email not found"})
        
    
    def save(self):
        user = self.context['request'].user
        if not user.is_authenticated:
            raise serializers.ValidationError({"detail": "User is not authenticated"})
    
        # Get or create the user's wallet object
        wallet, created = Wallet.objects.get_or_create(user=user)
        #wallet = Wallet.objects.get(user=user)
        data = self.validated_data
        url = 'https://api.paystack.co/transaction/initialize'
        headers = {                
                "authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
            }

        try:
            r = requests.post(url, headers=headers, data=data)
            r.raise_for_status()  # Raises an exception if the response has an error status code
            response = r.json()
        except requests.exceptions.RequestException as e:
            raise serializers.ValidationError({"detail": f"Error: {str(e)}"})

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type="deposit",
            amount= data["amount"],
            paystack_payment_reference=response['data']['reference'],
            status="pending",
        )

        return response

    
    