import re
from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from apps.accounts.models import User, UserRole, OwnerProfile, PasswordResetToken, EmailVerificationToken

class OwnerProfileSerializer(serializers.ModelSerializer):
    masked_bank_account = serializers.ReadOnlyField(source='masked_account_number')

    class Meta:
        model = OwnerProfile
        fields = [
            'id',
            'business_name',
            'registration_number',
            'pan_gst_number',
            'address',
            'city',
            'locality',
            'bank_account_holder',
            'bank_account_number',
            'masked_bank_account',
            'bank_ifsc_code',
            'verification_status',
            'payout_enabled',
            'created_at',
            'updated_at'
        ]
        extra_kwargs = {
            'bank_account_number': {'write_only': True},
        }


class UserProfileSerializer(serializers.ModelSerializer):
    owner_profile = OwnerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'phone',
            'full_name',
            'role',
            'is_active',
            'is_verified',
            'avatar_url',
            'owner_profile',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'email', 'role', 'is_active', 'is_verified', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    role = serializers.ChoiceField(choices=[UserRole.CUSTOMER, UserRole.OWNER], default=UserRole.CUSTOMER)
    business_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    registration_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    pan_gst_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, default="Hyderabad")
    locality = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_email(self, value):
        normalized_email = value.lower().strip()
        if User.objects.filter(email=normalized_email).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return normalized_email

    def validate_phone(self, value):
        if value:
            clean_phone = re.sub(r'[\s\-()]', '', value)
            if User.objects.filter(phone=clean_phone).exists():
                raise serializers.ValidationError("An account with this phone number already exists.")
            return clean_phone
        return None

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        role = attrs.get('role')
        business_name = attrs.get('business_name')
        if role == UserRole.OWNER and not business_name:
            raise serializers.ValidationError({"business_name": ["Business name is required for Hall Owner registration."]})
        return attrs

    def create(self, validated_data):
        role = validated_data['role']
        business_name = validated_data.pop('business_name', '')
        registration_number = validated_data.pop('registration_number', '')
        pan_gst_number = validated_data.pop('pan_gst_number', '')
        city = validated_data.pop('city', 'Hyderabad')
        locality = validated_data.pop('locality', '')

        with transaction.atomic():
            user = User.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                full_name=validated_data['full_name'],
                phone=validated_data.get('phone'),
                role=role,
            )

            if role == UserRole.OWNER:
                OwnerProfile.objects.create(
                    user=user,
                    business_name=business_name,
                    registration_number=registration_number,
                    pan_gst_number=pan_gst_number,
                    city=city,
                    locality=locality,
                )

            # Generate initial email verification token
            EmailVerificationToken.create_for_user(user)

            return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"detail": "Invalid email or password."})

        if not user.check_password(password):
            raise serializers.ValidationError({"detail": "Invalid email or password."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Your account has been deactivated. Please contact support."})

        attrs['user'] = user
        return attrs


class UserProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    avatar_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    
    # Owner specific fields
    business_name = serializers.CharField(max_length=255, required=False)
    registration_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    pan_gst_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False)
    locality = serializers.CharField(max_length=100, required=False, allow_blank=True)
    bank_account_holder = serializers.CharField(max_length=150, required=False, allow_blank=True)
    bank_account_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    bank_ifsc_code = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def update(self, instance, validated_data):
        with transaction.atomic():
            if 'full_name' in validated_data:
                instance.full_name = validated_data['full_name']
            if 'phone' in validated_data:
                new_phone = validated_data['phone']
                if new_phone:
                    clean_phone = re.sub(r'[\s\-()]', '', new_phone)
                    if User.objects.filter(phone=clean_phone).exclude(id=instance.id).exists():
                        raise serializers.ValidationError({"phone": ["Phone number already in use by another user."]})
                    instance.phone = clean_phone
                else:
                    instance.phone = None
            if 'avatar_url' in validated_data:
                instance.avatar_url = validated_data['avatar_url']

            instance.save()

            if instance.is_owner and hasattr(instance, 'owner_profile'):
                profile = instance.owner_profile
                owner_fields = [
                    'business_name', 'registration_number', 'pan_gst_number',
                    'address', 'city', 'locality', 'bank_account_holder',
                    'bank_account_number', 'bank_ifsc_code'
                ]
                for field in owner_fields:
                    if field in validated_data:
                        setattr(profile, field, validated_data[field])
                profile.save()

            return instance


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
