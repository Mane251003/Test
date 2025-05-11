from django.contrib import admin
from tests.forms import AnswerInlineFormSet
from tests.models import Test, Question, Answer, Results, Trait, UserResponse, TestSession
import json
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet





class RequiredAnswerInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        question = self.instance
        if not question.question_type:
            # Ստուգում՝ առնվազն մեկ չջնջված ձեւ կա՞
            valid = False
            for form in self.forms:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    valid = True
                    break
            if not valid:
                raise ValidationError("Առնվազն մեկ պատասխան պետք է մուտքագրվի։")


class AnswerInline(admin.TabularInline):
    """Display answer fields inline Question model"""
    formset =RequiredAnswerInlineFormSet
    model = Answer
    extra = 0



class QuestionInline(admin.TabularInline):
    """Display question fields inline Test model"""
    model = Question
    extra = 0
    show_change_link = True
    def get_form(self, request, obj=None, **kwargs):
        """
        Եթե obj.category.slug == 'personality-assessment',
        ապա ցուցադրել trait, key, weight, question_type, scale_min, scale_max դաշտերը
        """
        form = super().get_form(request, obj, **kwargs)
        # Եթե obj բացարձակապես գոյություն ունի և ունի category
        if obj and obj.test.category.slug == 'personality-assessment':
            # Մաքրում ենք base_fields (թույլատրում ենք միայն ցանկալի դաշտերը)
            form.base_fields.clear()
            show = [
                'test', 'title', 'order', 'trait', 'key',
                'weight', 'question_type', 'scale_min', 'scale_max',
                'multiple_choices', 'open_text_prompt'
            ]
            for f in show:
                form.base_fields[f] = self.model._meta.get_field(f).formfield()
            return form
        # Եթե ոչ՝ ցույց ենք տալիս միայն question վելյունները
        return form



class TestAdmin(admin.ModelAdmin):
    """Display Test model fields in admin panel"""
    list_display = ('test_name', 'category', 'modified_date', 'created_date')
    search_fields = ('test_name', 'category__category_name')
    list_per_page = 20
    list_max_show_all = 100
    list_filter = ('category__category_name',)
    prepopulated_fields = {"slug": ("test_name",)}
    inlines = [QuestionInline]

            
class QuestionAdmin(admin.ModelAdmin):
    """Display Question model fields in admin panel"""
    list_display = ('question', 'test', 'question_type')

    
    search_fields = ('question',)
    list_per_page = 20
    list_max_show_all = 100
    list_filter = ('test__test_name',)
    inlines = [AnswerInline]
    fieldsets = (
        (None, {
            'fields': ('test', 'question', 'order','key','trait', 'weight', 'question_type')
        }),

        ('Multiple Choice Options', {
            'fields': ('multiple_choices',),
            'classes': ('collapse',),
            'description': 'Լրացրեք ընտրանքները JSON ձևաչափով'
        }),
        ('Open Text Options', {
            'fields': ('open_text_prompt',),
            'classes': ('collapse',),
            'description': 'Լրացրեք հրահանգները'
        }),
        ('Rating Scale Options', {
            'fields':('scale_min', 'scale_max'),
            'classes':('collapse',),
            'description': 'Ընտրեք բալային համակարգը'
        })
        
    )
    def get_fields(self, request, obj=None):
        
        fields = super().get_fields(request, obj)
        if obj:
            if obj.question_type == 'yes_no':
               
                fields = [f for f in fields if f not in ('open_text_prompt', 'scale_min', 'scale_max')]
            elif obj.question_type == 'multiple_choice':
                fields = [f for f in fields if f not in ('open_text_prompt', 'scale_min', 'scale_max')]
            elif obj.question_type == 'open_text':
                fields = [f for f in fields if f not in ('multiple_choices', 'scale_min', 'scale_max')]
            elif obj.question_type == 'rating_scale':
                fields = [f for f in fields if f not in ('multiple_choices', 'open_text_prompt')]

        return fields
    

    def get_readonly_fields(self, request, obj=None):
        readonly_fields=super().get_readonly_fields(request, obj)
        if obj and obj.question_type == 'yes_no':
            return list(readonly_fields)+['multiple_choices']
        return readonly_fields




    def save_model(self, request, obj, form, change):
        """Auto-populate yes/no options and validate data"""
        if obj.question_type == 'yes_no':
            
            obj.multiple_choices =json.dumps([{"text": "Այո", "value": 1}, {"text": "Ոչ", "value": 0}])
            obj.open_text_prompt = None
            obj.scale_min=None
            obj.scale_max=None
        elif obj.question_type=='multiple_choice':
            obj.open_text_prompt=None
            obj.scale_min=None
            obj.scale_max=None

        elif obj.question_type=='open_text':
            obj.multiple_choices=None
            obj.scale_min=None
            obj.scale_max=None           
        
        elif obj.question_type=='rating_scale':
            obj.multiple_choices=None
            obj.open_text_prompt=None
            
        # Validate the model instance before saving
 
        try:
            obj.full_clean()
        except ValidationError as e:
            form.add_error(None, e)
            raise

        super().save_model(request, obj, form, change)
        





    def get_fieldsets(self, request, obj=None):
        if obj and obj.test.category.category_name == 'Personality Assessment':
            return self.fieldsets
        return super().get_fieldsets(request, obj)
    class Media:
        js = ('js/admin/question_type_handler.js',)


class AnswerAdmin(admin.ModelAdmin):
    """Display Answer model fields in admin panel"""
    list_display = ('answer', 'answer_image', 'question', 'is_correct')
    list_per_page = 20
    list_max_show_all = 100


class ResultsAdmin(admin.ModelAdmin):
    """Display Results model in admin panel"""
    list_display = ('user', 'category', 'test', 'correct_answer_count', 'wrong_answer_count',
                    'correct_answer_percent', 'created_at', 'updated_at')
    search_fields = ('user__email',)




class TestSessionAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'test', 'start_time', 'end_time', 'duration')
    list_filter = ('test', 'start_time')
    search_fields = ('candidate__email', 'test__title')

class UserResponseAdmin(admin.ModelAdmin):
    list_display = ('session', 'question', 'value')
    raw_id_fields = ('session', 'question')

admin.site.register(Test, TestAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(Results, ResultsAdmin)
admin.site.register(Trait)
admin.site.register(UserResponse)
admin.site.register(TestSession)