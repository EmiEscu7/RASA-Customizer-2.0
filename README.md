# RASA Customizer 2.0
### Objetivo:
El objetivo de este proyecto es a partir de un mensaje generico, generar un template acorde a la personalidad conservando la intención del mensaje

#### Su uso:
Recomendación: Entrenar el componente antes de ejecutarlo, usar `rasa train` 

Para utilizar Rasa Customizer hay que ejecutar el componente de RASA, para eso utilizar: `rasa run -p <port> --enable-api --cors "*" --debug`
Ejemplo: `rasa run -p 5005 --enable-api --cors "*" --debug`
> Nota: Estos comandos deben ser ejecutados desde consola estando en la ubicación del componente de rasa, ejemplo: D:\Universidad\Rasa-Customizer-2.0 >

A su vez el componente trabaja con un custom channel llamado rest_custom, basado en rest.py desarrollado por RASA. Para realizar el request.post al componente hay que tener una consideración en la URL ya que se envian los mensajes por éste channel. 
Template URL: `http://localhost:<bot_port>/webhooks/rest_custom/webhook`
bot_port hace referencia al puerto donde se encuentra ejecutando el componente. 
Ejemplo URL: `http://localhost:5005/webhooks/rest_custom/webhook`

El output a este request.post será el texto plano listo para ser formateado en python.

#### Ayuda extra
test.py contiene ejemplo de como debe ser la comunicación y cual será el output

#### Desarrollado con las siguientes versiones:
- Version Rasa: 2.4.0 
- Version Rasa.SDK: 2.6.0
- Version Python: 3.7.9