//g++ -Wall -o Server -std=c++11 Server.cpp utility.cpp
//Copyright @ David Fucking Berger
//Anmerkungen zu Kommentaren: entweder man weiß wie Sockets und Read()/Write() in c/c++ funktionieren oder halt nicht, dann einfach mal kurzes Tutorial googlen, dauert wenn man c/c++ kann vielleicht 30min
//Die spezifischen, nicht selbsterklärenden Teile wie Datenformate etc. sollten eigentlich schon angegeben sein. Fragen bitte einfach an david.p.berger@gmx.de
//||UPDATE|| Ich hab jetz doch alles dokumentiert -.-
#define INTERVALL 1000000	//1s
#define READTIMEOUT 1		//1s
#define WRITETIMEOUT 1		//1s

#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <string>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <iostream>
#include <unistd.h>
#include <time.h>
#include <sys/time.h>
#include <ctime>
#include <chrono>
#include <sys/stat.h>//----------------
#include <fcntl.h> //-----------------
#include <iomanip>
#include "utility.h"

using namespace std;

int newsockfd = 0;
int RegenRinne1 = 0;
int RegenRinne2 = 0;
int KameraWolken1 = 0;
int KameraWolken2 = 0;
const char* WritePipe = "/tmp/RegenRinne1";
const char* ReadPipe = "/tmp/RegenRinne2";
const char *WritePipeCam = "/tmp/camin";
const char *ReadPipeCam = "/tmp/camout";
double buf;

void CleanUp()	//Zeug schließen
{
    if (newsockfd != 0)
   	 close(newsockfd);
}
//Versucht ein Double Array der Länge 5 an Client zu senden
//return value: -1 Fehler; 1 Erfolg
int DatenSenden(int sockfd, double Daten[5]) {
    int n;
    char *buffer = (char*)&Daten[0];
    if ((n = write(sockfd, buffer, 40)) < 0)
    {
   	 error("ERROR beim Senden der Daten");
   	 return -1;
    }
    cout <<currentTime()  <<"Daten gesendet" << endl;
return 1;
}
//Versucht ein einzelnes byte Client zu senden
//return value: -1 Fehler; 1 Erfolg
int BefehlSenden(int sockfd, char Befehl) {
    int n;
    if ((n = write(sockfd, (void *)&Befehl, 1)) < 0)
    {
   	 error("ERROR beim Senden eines Befehls");
   	 return -1;
    }
    cout <<currentTime() <<"Befehl " << (int)Befehl << " gesendet" << endl;
return 1;
}
//schickt ein byte Anfrage an pipe sockfd und erhält einen double von pipe sockfd2
//Gibt 420 bei Fehler zurück
double DatenEmpfangen(int sockfd, int sockfd2) {
    double buffer;
    unsigned char shakebyte = 0xff;
    int n;
    if ((n = write(sockfd, &shakebyte, 1)) <= 0)
    {
   	 error("ERROR beim Handshake mit einem Sensor");
   	 return 420;
    }
	n = read(sockfd2, (void *)&buffer,8);
    if (n <= 0)
    {
   	 error("ERROR beim Empfangen der Sensordaten");
   	 return 420;
    }
    cout <<currentTime() <<"SensorDaten " << (double)buffer << " empfangen" << endl;
    return buffer;
}
//empfängt ein einzelnes byte von Socket sockfd
//return value 0xfe bei Fehler (z.B Timeout), weil das byte auch vom client gesendet wird wenn er absichtlich disconnected
unsigned char BefehlEmpfangen(int sockfd) {
    char buffer;
    int n;
	n= read(sockfd, (void *)&buffer,1);
    if (n <= 0)
    {
   	 error("ERROR beim Empfangen des Befehls");
   	 return 0xfe;
    }
    cout <<currentTime() <<"Befehl " << (int)buffer << " empfangen" << endl;
    return buffer;
}

int main(int argc, char *argv[]) {
	//Funktion CleanUp beim schließen aufrufen, damit der Socket geschlossen und der Port wieder frei ist
    atexit(CleanUp);
    //"Handle" für den Socket
    int sockfd;
    //Der Port auf dem auf einen client gewartet wird
    int portno = 5902;
    //länge der client adresse (wenn 0 connect Fehlgeschlagen)
    int clilen;
    //eigene und client adresse
    struct sockaddr_in serv_addr, cli_addr;
    //Der letze Befehl...
    char letzerBefehl = 0;
    cout <<currentTime() << "Port #" << portno << endl;
    //öffne einen Socket für internet
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    int option = 1;
    //wenn auf linux sockets nicht mit close() geschlossen werden, bleibt der port für ca. 4 min belegt und das erneute Starten des servers schlägt fehl
    //--> REUSEADDR ; sofort den port wieder freigeben
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &option, sizeof(option));
    if (sockfd < 0)
   	 error("ERROR beim Socket öffnen");
   	 //server adresse mit nullern vollschreiben, falls noch schmarrn im allocated memory steht
    bzero((char *)&serv_addr, sizeof(serv_addr));
    //hatten wir ja schon...
    serv_addr.sin_family = AF_INET;
    //parsed ips und ddns server und alles halt
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    //port setzen
    serv_addr.sin_port = htons(portno);
    //Socket an port und adresse binden
    if (bind(sockfd, (struct sockaddr *) &serv_addr,
   	 sizeof(serv_addr)) < 0)
   	 error("ERROR beim Binden");
   	 //maximal eine connection annehmen
    listen(sockfd, 1);
    //länge der clientadresse setzen
    clilen = sizeof(cli_addr);
    //reconnect loop:
    //Warten auf Verbindung von Client, daten austauschen, bei fehler disconnecten und wieder warten
    while (1) {
	connect:
   	 cout <<currentTime() << "Warte auf Verbindung..." << endl;
   	 //einen Client akzeptieren und sein handle in newsockfd speichern
   	 if ((newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr, (socklen_t*)&clilen)) < 0)
   		 error("ERROR beim Annehmen der Verbindung");
   		 
   		 //Timeout erklärt sich von selbst
	struct timeval timeout;      
    	timeout.tv_sec = READTIMEOUT;
    	timeout.tv_usec = WRITETIMEOUT;
    	if (setsockopt (newsockfd, SOL_SOCKET, SO_RCVTIMEO, (char *)&timeout,
                sizeof(timeout)) < 0)
        	error("setsockopt fehlgeschlagen\n");

    	if (setsockopt (newsockfd, SOL_SOCKET, SO_SNDTIMEO, (char *)&timeout,
                sizeof(timeout)) < 0)
        	error("setsockopt fehlgeschlagen\n");
   	 cout <<currentTime() << "Client verbunden" << endl;
   	 while (1) {
		 //die pipes jedes mal öffnen, wenn sie schon offen sind machts keinen unterschied
		 //es kann sein, dass die pipe zwischendurch zu is, deswegen eine art reconnect versuch
		 //leider kann man nicht testen, ob die pipe noch verbunden ist, also lieber nummer sicher
		 RegenRinne1 = open(WritePipe, O_RDWR | O_NONBLOCK);	//RegenPipe zum Schreiben
		 RegenRinne2 = open(ReadPipe,O_RDWR | O_NONBLOCK);		//-"- zum lesen
		 KameraWolken1 = open(WritePipeCam, O_RDWR | O_NONBLOCK);    //Kamera-Pipe
         KameraWolken2 = open(ReadPipeCam, O_RDWR | O_NONBLOCK);
		 //Sendeintervall warten
   		 usleep(INTERVALL);
   		 //client sollte ein byte senden, in dem paar sachen stehn
   		 letzerBefehl = BefehlEmpfangen(newsockfd);
   		 switch (letzerBefehl)
   		 {
   		 case 0xff://Daten Senden versuchen bei 0xff, weil das halt so is
   			 double d[5];
   			 d[0] = ((int) DatenEmpfangen(KameraWolken1, KameraWolken2)) / 100;	//Wolkenverdeckung
   			 d[1] = DatenEmpfangen(RegenRinne1,RegenRinne2);		//Regen
   			 d[2] = rand() * 324872.123;							//Windgeschwindigkeit
   			 d[3] = rand() * 123.45;								//Himmelshelligkeit
   			 d[4] = rand() * 0.00123;								//Himmelsqualität
   			 //returnwert von datensenden sollte optimalerweise nicht -1 sein
   			 if (DatenSenden(newsockfd, d)==-1)
				goto connect;		//wartet auf neuen client, weil senden fehlgeschlagen ist
   			 if(BefehlSenden(newsockfd, 0xff)==-1)//sagt dem client bescheid, dass der server wieder bereit und noch da ist
				goto connect;	//Scheiße gelaufen, client nicht mehr erreichbar --> reconnect
   			 break;
   		 case 0xfe:	//das sendet der client, wenn er planmäßig beendet wird
   			 cout<<currentTime()  << "Client hat Verbindung beendet" << endl;
   			 goto connect;
   		 default:
   			 cout <<currentTime() << "unbekannten Befehl erhalten" << endl;
   			 break;
   		 }
   	 }
    }
    return 0;
}
