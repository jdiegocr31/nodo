#!/usr/bin/env python
# encoding: utf-8

#Linea 1 - “Shebang”,le indicamos a la máquina con qué programa lo vamos a ejecutar.
#Linea 2 - Python 2.7 - asume que solo se utiliza ASCII en el código fuente
# para usar utf-8 hay que indicarlo al principio de nuestro script encoding: utf-8


import rospy                                                    #Importamos ropsy (interface de python-ROS)
from sensor_msgs.msg import LaserScan                           #Importamos el tipo de mensaje Lasersan
from geometry_msgs.msg import Twist                             #Importamos el tipo de mensaje Twist
import random

from std_msgs.msg import String             #Importamos el tipo de mensaje String      
from settings import GAIT_COMMANDER_CIPHER  #Importamos el diccionario Gait Commander
import time    

#Definimos Constantes
MIN_DIST = 0.75      #Distancia Mínima para detectar obstáculos = 75 cm
MAX_DIST = 3.5      #Distancia Máxima = 3.5 metros

#Definimos Variables
left = ahead = right = 1.0  #valores mínimos de cada región del láser
linear_x = 0.5              #velocidad lineal = 0.5 m/s
angular_z = 0.5             #velocidad angular = 0.5 rad/seg

'''
 Función callback - Procesa las 240 muestras del láser para detectar obstáculos
 y nos devuelve el valor mínimo de las áreas de la derecha,izquierda y enfrente 
 del láser del robot

'''

def callback(mensaje):

    #Declaración de variables globales
    global left, ahead, right
    
    scan_range = [] #Definimos una lista vacía

    for i in range(len(mensaje.ranges)):
        if mensaje.ranges[i] == float('Inf'): #Si el sensor no detecta nada 
            scan_range.append(MAX_DIST)        #le asigamos un valor de 3.5m
        else:
            scan_range.append(mensaje.ranges[i]) #Si tiene un valor, lo agregamos a nuestra lista scan_range

    #Regiones = 240/3 = 80 muestras

    right = min(scan_range[0:79]) #muestras de 0:79
    ahead = min(scan_range[80:159]) #muestras de 80:159
    left = min(scan_range[160:239]) #muestras de 160:239

    # print("Left = %f , Ahead = %f , Right = %f" % (left,ahead,right))

    
def nodo():                                    # Definimos una función nodo

    rospy.init_node('nodo_mini_guepardo')   # Inicializamos nuestro nodo y le asignamos un nombre = nodo_detect_obstacles

    
    '''
    Para procesar la data del láser del robot nos subcribimos al tópico /scan
    Creamos la variable scan_sub que es de tipo Subscriber
    '''
                                #Name Topic|tipo de mensaje|función
    scan_sub = rospy.Subscriber('/scan', LaserScan, callback)

    '''
    Como nuestro robot va a realizar movimientos, creamos la variable velocity_publisher que es de tipo publisher
    y publicamos el tópico /base_controller/command
    '''   
                                    # Name Topic   |tipo de mensaje| # límite de 10 mensajes en cola 
    command_pubber = rospy.Publisher("state_change", String, queue_size = 10)

    rate = rospy.Rate(10) #10Hz

    while not rospy.is_shutdown():  

        move_mini_guepardo = "i" #Definimos una variable de tipo String y la inicializamos con "i" (Idle o inactivo)

        action_description = ''  #Definimos una variable de tipo String, para almacenar el tipo de movimiento del robot
        
        #Condiciones del robot cuando detecta un obstáculo menor a 1 metro

        #1- El robot irá hacia adelante, por que el láser no detecta ningún obstáculo a una distancia menor a 1 metro.
        if (left > MIN_DIST and ahead > MIN_DIST and right > MIN_DIST):
            action_description = 'Forward' #Asignamos el tipo de movimiento
            move_mini_guepardo = "ts"

        #2- El robot gira hacia la derecha, por que el láser detecta un obstáculo 
        #   a una distancia menor a 1 metro a la izquierda del robot.
        elif left < ahead and left < right and left < MIN_DIST:
            action_description = 'Turn right'   #Asignamos el tipo de movimiento            
            move_mini_guepardo = "tr"

        #3- El robot dará marcha atrás, porque el láser detecta un obstáculo 
        #   a una distancia menor a 1.0 metro, enfrente del robot.
        elif ahead < left and ahead < right and ahead < MIN_DIST:
            action_description = 'Backforward'  #Asignamos el tipo de movimiento
            move_mini_guepardo = "tb"
            
        #4- El robot gira hacia la izquierda, por que el láser detecta un obstáculo 
        #   a una distancia menor a 1.0 metro a la derecha del robot.
        elif right < left and right < ahead and right < MIN_DIST:
            action_description = 'Turn left' #Asignamos el tipo de movimiento            
            move_mini_guepardo = "tl"
        else:
            action_description = 'unknown case' #Asignamos el tipo de movimiento

        rospy.logwarn(action_description)  #Imprimimos el tipo de movimiento en pantalla

        '''
        Para evitar que nuestro robot entre en un bucle infinito cuando
        realiza un movimiento hacia atrás, realizamos un movimiento adicional
        random hacia la derecha o hacia la izquierda con una pausa de 1 seg. - time.sleep(1.0)
        '''
        
        if move_mini_guepardo == "tb":
            
            command_pubber.publish(GAIT_COMMANDER_CIPHER["i"])   
            command_pubber.publish(GAIT_COMMANDER_CIPHER[move_mini_guepardo])         
                                                        
            if random.random() > 0.5:               
               command_pubber.publish(GAIT_COMMANDER_CIPHER["tr"])  #Gira hacia la derecha 
               time.sleep(1.0)
            else:
               command_pubber.publish(GAIT_COMMANDER_CIPHER["tl"])  #Gira hacia la izquierda
               time.sleep(1.0)
        else:
            command_pubber.publish(GAIT_COMMANDER_CIPHER[move_mini_guepardo])        
                                                    
        rate.sleep()                         #Loop 10 times per second


if __name__ == '__main__':                   # Llamamos a la función principal main
    try:
        nodo()                               # Lamamos a la función nodo    
    except rospy.ROSInterruptException :     # Check si hay una excepción - Ctrl-C para terminar la ejecución del nodo
        pass

