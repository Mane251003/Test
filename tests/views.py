from django.shortcuts import render, get_object_or_404, redirect
from category.models import Category
from tests.models import Test, Question, Answer, Results, UserResponse, TestSession
from tests.scoring import BigFiveScorer
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)
from django.db import transaction

def tests(request, category_slug=None):
    """Render tests.html file"""
    categories = None
    all_tests = None

    if category_slug is not None:
        categories = get_object_or_404(Category, slug=category_slug)
        all_tests = Test.objects.filter(category=categories)
        test_count = all_tests.count()
    else:
        all_tests = Test.objects.all()
        test_count = all_tests.count()

    context = {
        'all_tests': all_tests,
        'test_count': test_count
    }
    return render(request, 'tests/tests.html', context)


def test_description(request, category_slug, test_slug):
    """Render test_description.html file"""
    try:
        single_test = Test.objects.get(category__slug=category_slug, slug=test_slug)
        question_list = Question.objects.filter(test__slug=test_slug)


        test_session, created= TestSession.objects.get_or_create(
            candidate=request.user,
            test=single_test,
            end_time__isnull=True,
            defaults={'start_time': timezone.now()}
        )

        request.session['correct_answers'] = 0
        request.session['wrong_answers'] = 0
        request.session['current_session_id'] = test_session.id

    except Exception as e:
        raise e

    context = {
        'single_test': single_test,
        'first_question_id': question_list[0].pk,
        'test_question_amount': len(question_list),
        'session_id': test_session.id
    }
    return render(request, 'tests/test_description.html', context)


def question_details(request, category_slug, test_slug, question_id):
    """Render question_details.html file. Show questions with answers one by one on separate page"""
    if request.user.is_authenticated:
        try:
            session_id = request.session.get('current_session_id')
            if not session_id:
                return redirect('test_description', category_slug=category_slug, test_slug=test_slug)
            
            test_session = get_object_or_404(TestSession, pk=session_id)
            single_test = Test.objects.get(category__slug=category_slug, slug=test_slug)
           
            question_list = Question.objects.filter(test__slug=test_slug).order_by('order')

            id_list = list(question_list.values_list('id', flat=True))

            current_question_id = int(request.GET.get('id', question_id))
            try:

                pk_idx = id_list.index(current_question_id)
            except ValueError:
                return redirect('test_description', category_slug=category_slug, test_slug=test_slug)

                

            if pk_idx == len(question_list) - 1:
                last_question = True
                next_question_id = question_list[pk_idx].pk
            else:
                last_question = False
                next_question_id = question_list[pk_idx + 1].pk
            
            question = get_object_or_404(Question, pk=question_id)
            answers = Answer.objects.filter(question__pk=question_id)
            
            context = {
                'single_test': single_test,
                'question': question,
                'answers': answers,
                'next_question_id': next_question_id,
                'last_question': last_question,
                'current_question_number': pk_idx + 1,
                'test_question_amount': len(question_list),
                'category_slug': category_slug,
                'test_slug': test_slug,
                'session_id': session_id
            }

            if request.method == 'POST':
                previous_question_id = request.META.get('HTTP_REFERER').split('=')[1]
                previous_question = Question.objects.get(pk=int(previous_question_id))

                if previous_question.question_type == 'rating_scale':
                    rating_value = float(request.POST.get('rating_value', 0))
                    UserResponse.objects.update_or_create(
                       session=test_session,
                       question=previous_question,
                       value=rating_value
                    )
                
                    # For rating questions, count as correct if answered
                    request.session['correct_answers'] += 1
                
                elif previous_question.question_type in ['yes_no', 'multiple_choice']:
                    answers = Answer.objects.filter(question__pk=previous_question_id)
                    id_list = request.POST.getlist('boxes')
                    checked_answers = [Answer.objects.get(pk=int(answer_id)) for answer_id in id_list]
                    correct = all([answer.is_correct for answer in checked_answers])
                    unchecked_answers = [answer.is_correct for answer in answers if answer not in checked_answers]
                    #question = Question.objects.get(pk=int(previous_question_id))

                    if correct and True not in unchecked_answers:
                       request.session['correct_answers'] += 1
                    else:
                       request.session['wrong_answers'] += 1

                
              #  answers = Answer.objects.filter(question__pk=int(previous_question_id))

               
    

                if 'last' in request.POST:
                    test_session.end_time = timezone.now()
                    test_session.save()
                    """
                    big_five_scorer=BigFiveScorer(test_session)
                    results=big_five_scorer.calculate_results()
                    print(f"results is {results}")
                    #p rint(f"results interpretation items is {results['interpretation'].items()}" )                                                                                         
                
                    Results.objects.update_or_create(
                       session=test_session,
                       defaults={
                          'raw_scores': results['raw_scores'],
                          'normalized_scores': results['normalized_scores'],
                          'interpretation': results['interpretation'],
                          'recommendations': results['recommendations'],
                          'theoretical_scores': results.get('theoretical_scores', {}),
                          'scale_evaluations': results.get('scale_evaluations', {}),
                          'scenario_analysis': results.get('scenario_analysis', {}),
                          'general_description':results['general_description']
                        }
                    )"""
                    return redirect('results', category_slug=category_slug, test_slug=test_slug)
                else:
                    return render(request, 'tests/question_details.html', context)
            else:
                return render(request, 'tests/question_details.html', context)

        except Exception as e:
            raise e
    else:
        return redirect('login')


def results(request, category_slug=None, test_slug=None):
    """Show test results on separate page. Save results to database."""
    try:
        # Ստանալ ընթացիկ թեստի սեսիան
        session_id = request.session.get('current_session_id')
        test_session = TestSession.objects.get(pk=session_id)
        test=test_session.test

        
        question_list = Question.objects.filter(test__slug=test_slug)
        test_question_amount = len(question_list)

        # Ստեղծել արդյունքների օբյեկտ
        data = Results()
        data.session = test_session  # Ավելացնել session-ի հղումը
        data.user = request.user
        data.category = Category.objects.get(slug=category_slug)
        data.test = Test.objects.get(slug=test_slug)
        data.correct_answer_count = request.session.get("correct_answers", 0)
        data.wrong_answer_count = request.session.get("wrong_answers", 0)
        
        if test_question_amount > 0:
            data.correct_answer_percent = f'{round((data.correct_answer_count / test_question_amount) * 100)}%'
        else:
            data.correct_answer_percent = "0%"
        
        data.save()
        context = {
                'category_slug': category_slug,
                'test_slug': test_slug,
                'test_question_amount': test_question_amount,
                'data': data,
                'question_list': question_list,
                'test_session': test_session,
                'session_id':session_id,
                'test': test,
                'is_big5': test.test_name.lower()== 'big five personality test' 
            }



        if context['is_big5']:
            # Ստեղծել BigFiveScorer օբյեկտ
            big_five_scorer = BigFiveScorer(test_session)
            results = big_five_scorer.calculate_results()
            data.raw_scores = results['raw_scores']
            data.normalized_scores = results['normalized_scores']
            data.interpretation = results['interpretation']
            data.recommendations = results['recommendations']
            data.theoretical_scores = results.get('theoretical_scores', {})
            data.scale_evaluations = results.get('scale_evaluations', {})
            data.scenario_analysis = results.get('scenario_analysis', {})
            data.general_description=results['general_description']
            data.save()

            context.update({
                'interpretation': data.interpretation,
                'general_description': data.general_description
            })
            print(f"results interpretation items is {data.interpretation.items()}" )
            print(f"general description is {data.general_description.items()}")


        # Մաքրել session տվյալները
        del request.session['current_session_id']
        del request.session['correct_answers']
        del request.session['wrong_answers']

        return render(request, 'tests/results.html', context)

    except TestSession.DoesNotExist:
        return redirect('test_description', category_slug=category_slug, test_slug=test_slug)
    except Exception as e:
        # Լոգավորել սխալը եւ ցույց տալ error page
        logger.error(f"Error generating results: {str(e)}")
        return render(request, 'tests/error.html', {'error_message': str(e)})


def resultssss(request, category_slug=None, test_slug=None):
    
    
    """Show test results on separate page. Save results to database."""
    question_list = Question.objects.filter(test__slug=test_slug)
    test_question_amount = len(Question.objects.filter(test__slug=test_slug))

    data = Results()
    data.user = request.user
    data.category = Category.objects.get(slug=category_slug)
    data.test = Test.objects.get(slug=test_slug)
    data.correct_answer_count = request.session.get("correct_answers")
    data.wrong_answer_count = request.session.get("wrong_answers")
    data.correct_answer_percent = f'{round(request.session.get("correct_answers") * 100 / test_question_amount)}%'
    data.save()

    context = {
        'category_slug': category_slug,
        'test_slug': test_slug,
        'test_question_amount': test_question_amount,
        'data': data,
        'question_list': question_list,
    }
    return render(request, 'tests/results.html', context)


def calculate_results(session):
    responses = session.responses.select_related('question')
    # Հաշվարկի լոգիկան օգտագործելով session-ի պատասխանները


def resultsssssss(request, session_id):
    session=get_object_or_404(TestSession, id=session_id, candidate=request.user, is_completed=True)

    try:
        with transaction.atomic():
            scorer=BigFiveScorer(session)
            results=scorer.calculate_results()

            result, created = Results.objects.update_or_create(
                session=session,
                defaults={
                    'raw_scores': results['raw_scores'],
                    'normalized_scores': results['normalized_scores'],
                    'interpretation': results['interpretation'],
                    'recommendations': results['recommendations'],
                    'theoretical_scores': results.get('theoretical_scores', {}),
                    'scale_evaluations': results.get('scale_evaluations', {}),
                    'scenario_analysis': results.get('scenario_analysis', {}),
                    'general_description':results['general_description']

                }
            )
            
            #print(f"result interpretation items is {result.interpretation.items()}" )
            print(f"all desc is {result.general_description.items()}")
            user_promptt = request.GET.get("prompt", "")  
           # user_prompt=f"խնդրում եմ ընդհանուր ներկայացրու այս մարդուն , բնութագրումը կարդալու է գործատուն՝ աշխատանքի թեկնածուի համար, բնութագրիր հակիրճ, գրագետ, պարզ և հասկանալի, մի նշիր, որ ես քեզ տեղեկություն եմ տվել։  թեկնածուի բնութագրումն է {result.general_description.items()}"
            #ai_response = get_gemini_response(user_prompt) if user_prompt else ""

    except Exception as e:
        raise e
  

   
    return render(request, 'tests/results.html', {'data': result, 'session':session})
   
   
   

   
  #  result=get_object_or_404(Result, session=session)
 