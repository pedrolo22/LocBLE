Intrucciones para ejecución de software preparado para PC de Juan Carlos:

1. Abrir terminal en directorio y ejecutar "mqtt.sh"
	> sudo sh mqtt.sh

2. Abrir terminal en directorio y ejecutar "blescan.py" (necesita permisos de admin)
	> sudo python blescan.py

3. Abrir terminal en directorio y ejecutar "gestor_datos.py" 
	> sudo python gestor_datos.py

Con esto el sistema ya estaría generando y recibiendo datos a través de MQTT, para la calibración:

4. Abrir terminal en el directorio y ejecutar "calibracion.py"

	> sudo python calibracion.py -d JCportatil -t 60
	
Siendo: "-d" el nombre del dispositivo que está generando la calibración y "-t" el tiempo de calibración por zona.

Una vez ejecutado el script solicitará el número de dispositivo que va a generar la calibración, se debe introducir el id_dispositivo que en el caso del portátil de JC es el 3.

A partir de ese momento pedirá la zona en la que se comienza a calibrar y cada X tiempo volverá a pedir una zona para seguir con el etiquetado. Una vez se haya terminado la calibración parar el script con "ctrl+c" y los ficheros de calibración se habrán generado en el directorio "cal_files"

Espero que no se os complique mucho la tarea, cualquier problema me decís :)


