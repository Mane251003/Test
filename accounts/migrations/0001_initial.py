# Generated by Django 3.2.12 on 2025-05-05 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('first_name', models.CharField(max_length=50, verbose_name='Имя')),
                ('last_name', models.CharField(max_length=50, verbose_name='Фамилия')),
                ('username', models.CharField(max_length=50, unique=True, verbose_name='Имя пользователя')),
                ('email', models.EmailField(max_length=100, unique=True, verbose_name='Электронная почта')),
                ('phone_number', models.CharField(max_length=50, verbose_name='Телефон')),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')),
                ('last_login', models.DateTimeField(auto_now_add=True, verbose_name='Последний вход')),
                ('is_admin', models.BooleanField(default=False, verbose_name='Администратор')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Персонал')),
                ('is_active', models.BooleanField(default=False, verbose_name='Активный')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='Супер пользователь')),
            ],
            options={
                'verbose_name': 'Учетная запись',
                'verbose_name_plural': 'Учетные записи',
            },
        ),
    ]
