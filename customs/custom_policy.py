import zlib


import base64
import json
import sys
import logging
import random as rd
import numpy as np

from tqdm import tqdm
from typing import Optional, Any, Dict, List, Text

import rasa.utils.io
import rasa.shared.utils.io
from rasa.shared.constants import DOCS_URL_POLICIES
from rasa.shared.core.domain import State, Domain
from rasa.shared.core.events import ActionExecuted
from rasa.core.featurizers.tracker_featurizers import (
    TrackerFeaturizer,
    MaxHistoryTrackerFeaturizer,
)
from rasa.shared.nlu.interpreter import NaturalLanguageInterpreter
from rasa.core.policies.policy import Policy, PolicyPrediction
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.core.generator import TrackerWithCachedStates
from rasa.shared.utils.io import is_logging_disabled
from rasa.core.constants import MEMOIZATION_POLICY_PRIORITY
#importaciones nuevas
from rasa.core.channels.channel import InputChannel #clase que hace l rest. Me va a devolver la metadata
from rasa.core.policies.policy import confidence_scores_for, PolicyPrediction
from rasa.shared.nlu.constants import INTENT_NAME_KEY
from rasa.shared.core.events import SlotSet
from rasa.shared.nlu.constants import (
    ENTITY_ATTRIBUTE_VALUE,
    ENTITY_ATTRIBUTE_TYPE,
    ENTITY_ATTRIBUTE_GROUP,
    ENTITY_ATTRIBUTE_ROLE,
    ACTION_TEXT,
    ACTION_NAME,
    ENTITIES,
)
from rasa.shared.core.constants import (
    ACTION_LISTEN_NAME,
    LOOP_NAME,
    SHOULD_NOT_BE_SET,
    PREVIOUS_ACTION,
    ACTIVE_LOOP,
    LOOP_REJECTED,
    TRIGGER_MESSAGE,
    LOOP_INTERRUPTED,
    ACTION_SESSION_START_NAME,
    FOLLOWUP_ACTION,
)


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

     def vecinos(self, vector,familia):
        """
            Este algoritmo obtiene la distancia entre "vector" y todos los vectores de familia
            
            Retorna: Una distancia (mientras mas chica mejor, ya que queremos ver que tan parecidos son a los vectores que tenemos definidos como personalidad)
             
        """
        dist = 0
        a = np.array(vector)    
        for vector in familia:
            b = np.array(vector)
            dist += np.linalg.norm(a-b)

        return dist


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

        
        vector_personalities = []
        
        
        
        vector_personalities.append(diccionario[Neuroticism])
        vector_personalities.append(diccionario[Extraversion])
        vector_personalities.append(diccionario[Openness])
        vector_personalities.append(diccionario[Agreeableness])
        vector_personalities.append(diccionario[Conscientiousness])

        formal= vecinosFormal(vector_personalities)
        comun = vecinosComun(vector_personalities)
        informal= vecinosInformal(vector_personalities)

        if(formal < comun):
            if(formal < informal):
                return "_formal"
            else:
                return "_informal"
        else:
            if (comun < informal):
                return "_comun"
            else:
                return "_informal"

 

    def get_priority_mood(self):
        """
            La idea de esta funcion es que un algoritmo de machine learning determine
            la importancia que se le deba dar a c/u de los parametros que definen el 
            estado de animo de una persona. Actualmente devolvemos un vector con unos
            pesos determinados, que modelan los valores esperados del algoritmo
        """
        # pesos asignados a cada dimensión. 
        # [Neuroticism, Conscientiousness, Openness, Agreeableness, Extraversion]
        return [2, 1.5, 1, 1.5, 2]
