from django.db import models
from django.urls import reverse
from accounts.models import Account
from category.models import Category
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import json
from django.utils.timezone import now
from .validators import validate_options
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Trait(models.Model):
    CODE_CHOICES = [
        ('O', _('Openness')),
        ('C', _('Conscientiousness')),
        ('E', _('Extraversion')),
        ('A', _('Agreeableness')),
        ('N', _('Neuroticism')),
    ]
    code = models.CharField(max_length=1, choices=CODE_CHOICES, unique=True)
    name = models.CharField(max_length=20)
    description = models.TextField()
    low_range = models.TextField(help_text=_('Description for scores 0-40%'), blank=True)
    mid_range = models.TextField(help_text=_('Description for scores 40-60%'), blank=True)
    high_range = models.TextField(help_text=_('Description for scores 60-100%'), blank=True)
    reverse_scored = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Personality Trait")
        verbose_name_plural = _("Personality Traits")

    def __str__(self):
        return f"{self.get_code_display()} - {self.name}"

class Test(models.Model):

    """Create test model in database"""
    objects = models.Manager()

    test_name = models.CharField(max_length=255, unique=True, verbose_name='Наименование теста')
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True, verbose_name='Описание')
    test_image = models.ImageField(upload_to='photos/tests', verbose_name='Фото теста')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    modified_date = models.DateTimeField(auto_now=True, verbose_name='Дата изменений')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')

    class Meta:
        """Define how plural form looks in admin panel"""
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'

    def get_url(self):
        """Get reverse url for particular test"""
        return reverse('test_description', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.test_name




class Question(models.Model):
    """Create question model in database"""
    objects = models.Manager()

    TYPE_CHOICES = [
        ('yes_no', 'YES/NO'),
        ('multiple_choice', 'Multiple Choice'),
        ('open_text', 'Open Text'),
        ('rating_scale', '1-10 Rating Scale'),
    ]
    
    #test=models.ForeignKey(Test, related_name="questions", on_delete=models.CASCADE)
    question = models.TextField(verbose_name='Вопрос')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name='Наименование теста', related_name="questions")
    order=models.PositiveBigIntegerField(default=0) 
    trait=models.ForeignKey('Trait', on_delete=models.PROTECT, related_name='questions')
    key=models.CharField(max_length=1, choices=[('+', 'Positive'), ('-', 'Negative')], default='+')
    weight = models.FloatField(default=1.0, validators=[MinValueValidator(0), MaxValueValidator(1)],blank=True, null=True )
    question_type = models.CharField(
        max_length=50, 
        choices=TYPE_CHOICES, 
        default='yes_no',
        blank=True, 
        null=True
    )
    scale_min = models.IntegerField(
        blank=True,
        null=True,
        default=1,
        verbose_name= "Նվազագույն բալ"
    )
    scale_max = models.IntegerField(
        blank=True,
        null=True,
        default=10,
        verbose_name="Մաքսիմալ բալ"
    )
    multiple_choices = models.JSONField(
        blank=True,
        null=True,
        validators=[validate_options],
        help_text=_("Օրինակ՝ [{'text': 'Տարբերակ 1', 'value': 1}]")
    )
    open_text_prompt=models.TextField(
        blank=True,
        null=True,
        help_text="Մուտքագրեք հարցի հրահանգները"
    )
    def clean(self):
        super().clean()
        if self.question_type == 'yes_no':
            self.multiple_choices = json.dumps([{"text": "Այո", "value": 1}, {"text": "Ոչ", "value": 0}], ensure_ascii=False)
            self.open_text_prompt = None
            self.scale_max = None
            self.scale_min = None
        

        if self.question_type == 'rating_scale':
            if self.multiple_choices:
                raise ValidationError({'multiple_choices': 'Rating scale-ի դեպքում այս դաշտը պետք չէ'})
            if self.open_text_prompt:
                raise ValidationError({'open_text_prompt': 'Rating scale-ի դեպքում այս դաշտը պետք չէ'})
            if not (1 <= self.scale_min < self.scale_max <= 10):
                raise ValidationError({
                    'scale_min': '1-10 միջակայքում պետք է լինի',
                    'scale_max': '1-10 միջակայքում պետք է լինի'
                })


        if self.question_type == 'multiple_choice' and not self.multiple_choices:
            raise ValidationError({'multiple_choices': 'Մուտքագրեք պատասխանները JSON ձևաչափով'})
        
        if self.question_type == 'open_text' and not self.open_text_prompt:
            raise ValidationError({'open_text_prompt': 'Մուտքագրեք ձեր պատասխանը'})

    def save(self, *args, **kwargs):
        # Call clean to ensure validation and field setting
        self.clean()
        super().save(*args, **kwargs)

    def get_options(self):
        if self.question_type == 'yes_no':
            return [{"text": "Այո", "value": 1}, {"text": "Ոչ", "value": 0}]
        return self.multiple_choices if self.question_type == 'multiple_choice' else []


    @staticmethod
    def validate_options(value):
        try:
            if not isinstance(value, list) or len(value) < 2:
               raise ValidationError('Should be at least 2 optiosssssssssss')
            for item in value:
                if not isinstance(item, dict):
                   raise ValidationError('Each option must be a dictionary')
                if 'text' not in item or 'value' not in item:
                   raise ValidationError(_('Each option must have text and value fields'))
                if not isinstance(item['value'], (int, float)):
                   raise ValidationError(_('Value must be a number'))
        except (TypeError, ValueError):
            raise ValidationError(_('Invalid JSON format'))
        

    class Meta:
        """Define how plural form looks in admin panel"""
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return f"{self.question} ({self.get_question_type_display()}) "


class Answer(models.Model):
    """Create answer model in database"""
    objects = models.Manager()
    answer = models.CharField(max_length=200, verbose_name='Ответ')
    answer_image = models.ImageField(upload_to='photos/answers', default='default.jpg', verbose_name='Фото ответа')
    is_correct = models.BooleanField(default=False, verbose_name='Верно')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='Вопрос')


    class Meta:
        """Define how plural form looks in admin panel"""
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'

    def __str__(self):
        return self.answer if self.answer else f"Answer {self.id}"




class TestSession(models.Model):
    candidate=models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name='Candidate')
    test=models.ForeignKey(Test,on_delete=models.CASCADE)
    start_time=models.DateTimeField(auto_now_add=True, verbose_name='start time')
    end_time=models.DateTimeField(null=True, blank=True, verbose_name='end time')
    STATUS_CHOICES = [
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('expired', 'Expired')
]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')

    class Meta:
        verbose_name = "Test Session"
        verbose_name_plural = "Test Sessions"
        ordering = ['-start_time']

    
    def duration(self):
        if self.end_time:
            return self.end_time-self.start_time
        return None

class UserResponse(models.Model):
    session=models.ForeignKey(TestSession, related_name="responses", on_delete=models.CASCADE, verbose_name='Session')
    question = models.ForeignKey('Question', on_delete=models.CASCADE, verbose_name='Question')
    value = models.FloatField(verbose_name='Value')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created')

    class Meta:
        verbose_name = 'User Response'
        verbose_name_plural = 'User Responses'
        unique_together = ('session', 'question')

    def __str__(self):
        return f"{self.session.candidate.email} - {self.question.question[:50]}"
    

class Results(models.Model):
    """Create results model in database"""
    #For Big 5 test
    session=models.OneToOneField(TestSession, on_delete=models.CASCADE)
    raw_scores = models.JSONField(default=dict, blank=True, null=True)
    normalized_scores = models.JSONField(default=dict, blank=True)
    interpretation = models.JSONField(default=dict, blank=True)
    general_description=models.JSONField(default=dict, blank=True)
    recommendations = models.JSONField(default=dict, blank=True)
    theoretical_scores = models.JSONField(default=dict, blank=True)
    scenario_analysis = models.JSONField(default=dict)
    scale_evaluations = models.JSONField(default=dict)
    free_response_analysis = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)



    objects = models.Manager()
    user = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name='Пользователь')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name='Тест')
    correct_answer_count = models.IntegerField(verbose_name='Кол-во верных ответов')
    wrong_answer_count = models.IntegerField(verbose_name='Кол-во неверных ответов')
    correct_answer_percent = models.CharField(max_length=10, null=True, verbose_name='Процент правильных ответов')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата прохождения теста')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата повторного прохождения теста')

    def __str__(self):
        return self.test.test_name
    
    def get_trait_score(self, trait_code):
        return self.normalized_scores.get(trait_code, 0)


    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'
