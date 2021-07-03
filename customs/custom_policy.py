import numpy as np
import pandas as pd

from typing import Optional, Any, Dict, List, Text


from rasa.shared.core.domain import Domain

from rasa.core.featurizers.tracker_featurizers import (
    TrackerFeaturizer
)
from rasa.shared.nlu.interpreter import NaturalLanguageInterpreter
from rasa.core.policies.policy import Policy, PolicyPrediction
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.core.generator import TrackerWithCachedStates
from rasa.shared.utils.io import is_logging_disabled
from rasa.core.constants import MEMOIZATION_POLICY_PRIORITY

from rasa.core.policies.policy import confidence_scores_for, PolicyPrediction
from rasa.shared.nlu.constants import INTENT_NAME_KEY




# temporary constants to support back compatibility
MAX_HISTORY_NOT_SET = -1
OLD_DEFAULT_MAX_HISTORY = 5

class PersonalityPolicy(Policy):

    def __init__(
        self,
        featurizer: Optional[TrackerFeaturizer] = None,
        priority: int = MEMOIZATION_POLICY_PRIORITY,
        answered: Optional[bool] = None,
        **kwargs: Any,
        ) -> None:
        super().__init__(featurizer, priority, **kwargs)
        self.answered = False
        
    def train(
        self,
        training_trackers: List[TrackerWithCachedStates],
        domain: Domain,
        interpreter: NaturalLanguageInterpreter,
        **kwargs: Any,
    ) -> None:
        """Trains the policy on given training trackers.
        Args:
            training_trackers:
                the list of the :class:`rasa.core.trackers.DialogueStateTracker`
            domain: the :class:`rasa.shared.core.domain.Domain`
            interpreter: Interpreter which can be used by the polices for featurization.
        """
        pass

    def predict_action_probabilities(
        self,
        tracker: DialogueStateTracker,
        domain: Domain,
        interpreter: NaturalLanguageInterpreter,
        **kwargs: Any,
    ) -> PolicyPrediction:    

        sender_id = tracker.current_state()['sender_id']
        
        personality = self.get_personality(tracker)
        rta = self.generator_message(tracker, personality)
        
        if(self.answered):
            result = confidence_scores_for('action_listen', 1.0, domain)
            self.answered = False
        else:
            result = confidence_scores_for(rta, 1.0, domain)
            self.answered = True

        return self._prediction(result)



    def _metadata(self) -> Dict[Text, Any]:   
        return {
            "priority": self.priority,
        }
        
    @classmethod
    def _metadata_filename(cls) -> Text:
        return "scrum_master_policy.json"

    def get_personality(self, tracker:DialogueStateTracker):
        var = tracker.current_state()["latest_message"]
        metadata = var["metadata"]
        personality = metadata["personality"]
        return personality

    def generator_message(self, tracker: DialogueStateTracker, personality, sender = None):
        rta = ''
        intent = tracker.latest_message.intent.get(INTENT_NAME_KEY) 
        if(intent != "out_of_scope"): 
            style_answer = self.get_style_answer(personality)
            rta = 'utter_'
            rta += intent + style_answer
        return rta        

    def get_style_answer(self, personality) -> Text:  
        
        """ 
            Este metodo agarra los valores de cada atributo del diccionario pasado por parametro y en base a ellos, busca que perfil tiene mas similitud con ellos.

            Retorna: Un tipo de respuesta en base a la personalidad (String)
        """

        #Neuroticism": locura
        #"Extraversion": sociabilidad
        #"Openness": apertura a nuevas experiencias
        #"Agreeableness": buen trato con los demas
        #Conscientiousness: 0 cuidadoso, 1 diligente 
        
        vector_personalities = self.transform_dict_to_vector(personality)   

        neighbour = self.get_neighbour(vector_personalities) #obtiene el vector + parecido
        #neighbour = [nro,[numpyArray]]
        vector = np.take(neighbour, 1)
        return np.take(vector, len(vector)-1) #retorna si era "_formal" ó "_comun" ó "_informal"



    def get_priority_mood(self):
        """
            ----------SIN USO ACTUALMENTE----------
            La idea de esta funcion es que un algoritmo de machine learning determine
            la importancia que se le deba dar a c/u de los parametros que definen el 
            estado de animo de una persona. Actualmente devolvemos un vector con unos
            pesos determinados, que modelan los valores esperados del algoritmo
        """
        # pesos asignados a cada dimensión. 
        # [Neuroticism, Conscientiousness, Openness, Agreeableness, Extraversion]
        return [2, 1.5, 1, 1.5, 2]
    
    def get_neighbour(self, input) -> np.ndarray:
        """
            Este algoritmo obtiene la distancia entre "vector" y todos los vectores de familia
            Retorna: Una distancia (mientras mas chica mejor, ya que queremos ver que tan parecidos son a los vectores que tenemos definidos como personalidad)
             
        """
        
        input_numpy = np.array(input)
        
        min_dist_formal = self.compare_to_neighbour(input_numpy,"_formal")
        min_dist_informal = self.compare_to_neighbour(input_numpy,"_informal")
        min_dist_comun = self.compare_to_neighbour(input_numpy,"_comun")
        return (min(min_dist_comun,min_dist_formal,min_dist_informal))

    def compare_to_neighbour(self,vector_input:np.ndarray,neighbour:Text) -> list:
        
        dataframe_examples = pd.read_csv(r"examples_personalities.csv",sep=';')
        min_vector = dataframe_examples.values[0] #el primero del dataframe
        min_vector_no_string = np.array(np.delete(min_vector,min_vector.size -1))
        min_dist = 0
        cant = 0

        for example in dataframe_examples.values: #example = [1,1,1,1,1,STRING]
            if( str(np.take(example, len(example)-1)) == neighbour ):
                example_no_string = np.delete(example,example.size - 1) #quita el string
                dist_actual = np.linalg.norm(vector_input-example_no_string)
                if(min_dist < dist_actual):
                    min_vector = example
                min_dist += dist_actual
                cant+=1

        return [(min_dist/cant),min_vector]

    def transform_dict_to_vector(self, dict):
        vector = []
        vector.append(dict["Neuroticism"])
        vector.append(dict["Extraversion"])
        vector.append(dict["Openness"])
        vector.append(dict["Agreeableness"])
        vector.append(dict["Conscientiousness"])
        return vector