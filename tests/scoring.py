from collections import defaultdict
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from collections import defaultdict
from .models import TestSession, UserResponse, Trait, Question, Answer, Results
from django.utils.safestring import mark_safe
import logging
logger = logging.getLogger(__name__)



class BigFiveScorer:
    def __init__(self, session: TestSession):
        self.session=session
        print(f"session is {self.session}")

        # responses is a relative name in Response model 
        self.responses=session.responses.select_related('question__trait')
        print(f'responsesss is {self.responses}')
        self.trait_data=self._load_trait_definitions() #Extraversia, Neuroticism,Agreeableness,Conscientiousness,Openness

    


    #All codes,  Extraversia, Neuroticism,Agreeableness,Conscientiousness,Openness
    def _load_trait_definitions(self):
        traits=Trait.objects.all()
        return {t.code: t for t in traits}
    
    def _validate_session(self):
    #    if self.session.test.test_type!='BIG5':
     #       raise ValueError(_('This scorer works only with Big 5 test'))
        
        required_questions=self.session.test.questions.count()
        answered=self.responses.count()
        if answered!=required_questions:
            raise ValueError(_('Missing answers: %(answered)d/%(required)d') % {
                    'answered': answered,
                    'required': required_questions
                })
        
  #  @transaction.atomic
    def calculate_results(self):
        self._validate_session()

        trait_scores, max_scores=self._calculate_base_scores()
        normalized=self._normalize_scores(trait_scores, max_scores)

    
        return {
            'raw_scores': trait_scores,
            'max_scores': max_scores,
            'normalized_scores': normalized,

            'interpretation': self._generate_interpretation(normalized),
            'recommendations': {},
         #   'recommendations': self._generate_recommendations(normalized),
          #  'theoretical_scores': self._calculate_theoretical(),
           # 'scale_evaluations': self._calculate_scale_evaluations(),
             'general_description': self._general_description()
            
        }
    
   
    def _calculate_base_scores(self):
        trait_scores=defaultdict(float)
        max_scores=defaultdict(float)
        print('daa')

        for response in self.responses.select_related('question__trait'):
            question=response.question
            print(f"question is {question}")
            trait_code=question.trait.code  #extr, op, ..
            print(f"trait code is {trait_code}")
            print(f"base value is {response.value}")

            try:
               raw_value = self._calculate_raw_value(response, question)
               weighted_value = raw_value * question.weight
               trait_scores[trait_code] += weighted_value
               max_scores[trait_code] += self._get_max_score(question) * question.weight
            except (TypeError, ValueError) as e:
               # Լոգավորել սխալները
               logger.error(f"Error processing response {response.id}: {str(e)}")
        
        return dict(trait_scores), dict(max_scores)


    
    def _calculate_raw_value(self, response, question):
        base_value = response.value
        
        # Հակադարձ միավորում բացասական հարցերի համար
        if question.key == '-':
            if question.question_type == 'rating_scale':
                return (question.scale_max + question.scale_min) - base_value
            
            elif question.question_type in ['yes_no', 'multiple_choice']:
                max_val=self._get_max_score(question)
                return max_val-base_value
            
        return base_value

    def _get_max_score(self, question):
        if question.question_type == 'rating_scale':
            return question.scale_max
        elif question.question_type == 'yes_no':
            return 1
        elif question.question_type == 'multiple_choice':
            return max(choice['value'] for choice in question.multiple_choices)
        return 0
    
    def _normalize_scores(self, trait_scores, max_scores):
        return {
            code: (score/max_scores[code])*100
            for code, score in trait_scores.items()
            if max_scores.get(code, 0)>0
        }
    
    def _generate_interpretation(self, scores):
        return {
            code: self._trait_interpretation(code, score)
            for code, score in scores.items()
        }

    def _trait_interpretation(self, code, score):
        trait=self.trait_data[code]
    
        return {
                'name': trait.name,
                'score': round(score, 1),
                'description': self._get_description(trait, score),
                'graphic': self._generate_score_graphic(score)
            }
    
    def _get_description(self, trait, score):

        if score>=70:
            paragraphs=trait.high_range.split('\n\n')
            formatted_text=''.join(f'<p>{p}</p>' for p in paragraphs)
            print(f"high range is {trait.high_range}")
            return mark_safe(formatted_text)
            
        elif score<=30:
            paragraphs=trait.low_range.split('\n\n')
            formatted_text=''.join(f'<p>{p}</p>' for p in paragraphs)
            return mark_safe(formatted_text)
        
        elif score>30 and score<70:

            paragraphs=trait.mid_range.split('\n\n')
            formatted_text=''.join(f'<p>{p}</p>' for p in paragraphs)
            return mark_safe(formatted_text)
      
    def _general_description(self):
        trait_scores, max_scores=self._calculate_base_scores()
        normalized=self._normalize_scores(trait_scores, max_scores)
        interpretation=self._generate_interpretation(normalized)
        all_desc={}
        for code, data in interpretation.items():
          #  print(f"Data description {data['description']}")
            prompt=data['description']
            #ai_response=
            
            all_desc[code]=data['description']
      #  print(f"All desc is {all_desc.items()}")
        print(type(data['description']))
        print(f"type is {type(all_desc)}")

        return all_desc

        



    def _generate_score_graphic(self, score):
        bars = int(score / 5)
        return '▓' * bars + '░' * (20 - bars)

    def _generate_recommendations(self, scores):
        recommendations = []
        for code, score in scores.items():
            trait = self.trait_data[code]
            
            if score >= 70:
                recs = trait.high_considerations.split(', ')
            elif score <= 30:
                recs = trait.low_considerations.split(', ')
            else:
                continue
            recommendations.extend(recs)
            
        return list(set(recommendations))

    def _calculate_theoretical(self):
        scores = defaultdict(float)
        for response in self.responses.filter(question__question_type='multiple_choice'):
            try:
                selected = next(
                    c for c in response.question.multiple_choices
                    if c['value'] == int(response.choice)
                )
                scores[response.question.trait.code] += selected['value'] * response.question.weight
            except (StopIteration, ValueError, TypeError):
                continue
        return dict(scores)


    def _calculate_scale_evaluations(self):
        scale_data = defaultdict(list)
        for response in self.responses.filter(question__question_type='rating_scale'):
            scale_data[response.question.trait.code].append(response.scale_value) 
        
        return {
            code: sum(values)/len(values) if len(values)>0 else 0
            for code, values in scale_data.items()
        }

