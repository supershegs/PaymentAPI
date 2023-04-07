from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from django.conf import settings
import requests
from .models import Wallet, WalletTransaction, User
from .serializers import WalletSerializer, DepositSerializer
from django.contrib.auth.hashers import check_password
from .serializers import UserSerializer
from django.shortcuts import render


class Register(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class Login(APIView):
    permission_classes = ()

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        # Check if the username is valid
        if not username or not password:
            return Response({"error": "Please ensure you provide both username and password."}, status=status.HTTP_400_BAD_REQUEST)
    
        # Check if the user exists in the database
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "Invalid/wrong username and password "}, status=status.HTTP_401_UNAUTHORIZED)
    
        user = authenticate(username=username, password=password)
        if user is not None:
            if check_password(password, user.password):
                # Authentication successful, return token and username
                return Response({"token": user.auth_token.key, "username": username})
            else:
                #Password is invalid.
                return Response({"error": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)
            
        else:
            return Response({"error": "Wrong username or password"}, status=status.HTTP_401_UNAUTHORIZED)
        
class WalletInfo(APIView):
    
    def get(self, request):
        try:
            wallet = Wallet.objects.get(user=request.user)
            data = WalletSerializer(wallet).data
            return Response(data)
        except Wallet.DoesNotExist:
            return Response({"error": "No wallet found for this user."}, status=status.HTTP_404_NOT_FOUND)
       
            


class DepositFunds(APIView):
    
    def post(self, request):
        serializer = DepositSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            resp = serializer.save()
            return Response(resp)
        except Exception as e:
            print(str(e))
            return Response({"error": "Failed to deposit funds.", "rro": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        #resp = serializer.save()
        #return Response(resp)

class VerifyDeposit(APIView):

    def get(self, request, reference):
        transaction = WalletTransaction.objects.get(paystack_payment_reference=reference, wallet__user=request.user)
        reference = transaction.paystack_payment_reference
        url = 'https://api.paystack.co/transaction/verify/{}'.format(reference)
        headers = {
            
            "authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"             
            }
        r = requests.get(url, headers=headers)
        resp = r.json()
        if resp['data']['status'] == 'success':
            status = resp['data']['status']
            amount = resp['data']['amount']
            WalletTransaction.objects.filter(paystack_payment_reference=reference).update(status=status, amount=amount)
            return Response(resp)
        return Response(resp)
    
class index(APIView):
    def get(self, request):
        return render(request, 'index.html')
