//g++ -Wall -o Server -std=c++11 Server.cpp utility.cpp
//Copyright @ David Fucking Berger (alles halt)
//Anmerkungen zu Kommentaren: entweder man weiß wie Sockets und Read()/Write() in c/c++ funktionieren oder halt nicht, dann einfach mal kurzes Tutorial googlen, dauert wenn man c/c++ kann vielleicht 30min
//Die spezifischen, nicht selbsterklärenden Teile wie Datenformate etc. sollten eigentlich schon angegeben sein. Fragen bitte einfach an kilian.gampfer@t-online.de
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
const char* WritePipe = "/tmp/RegenRinne1";
const char* ReadPipe = "/tmp/RegenRinne2";
double buf;

void CleanUp()
{
    if (newsockfd != 0)
   	 close(newsockfd);
}

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
    atexit(CleanUp);
    int sockfd, portno = 5902, clilen;
    struct sockaddr_in serv_addr, cli_addr;
    char letzerBefehl = 0;
    cout <<currentTime() << "Port #" << portno << endl;
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    int option = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &option, sizeof(option));
    if (sockfd < 0)
   	 error("ERROR beim Socket öffnen");
    bzero((char *)&serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(portno);
    if (bind(sockfd, (struct sockaddr *) &serv_addr,
   	 sizeof(serv_addr)) < 0)
   	 error("ERROR beim Binden");
    listen(sockfd, 5);
    clilen = sizeof(cli_addr);
    while (1) {
	connect:
   	 cout <<currentTime() << "Warte auf Verbindung..." << endl;
   	 if ((newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr, (socklen_t*)&clilen)) < 0)
   		 error("ERROR beim Annehmen der Verbindung");
	struct timeval timeout;      
    	timeout.tv_sec = READTIMEOUT;
    	timeout.tv_usec = WRITETIMEOUT;

    	if (setsockopt (newsockfd, SOL_SOCKET, SO_RCVTIMEO, (char *)&timeout,
                sizeof(timeout)) < 0)
        	error("setsockopt failed\n");

    	if (setsockopt (newsockfd, SOL_SOCKET, SO_SNDTIMEO, (char *)&timeout,
                sizeof(timeout)) < 0)
        	error("setsockopt failed\n");
   	 cout <<currentTime() << "Client verbunden" << endl;
   	 while (1) {
		 RegenRinne1 = open(WritePipe, O_RDWR | O_NONBLOCK);	//RegenPipe
		 RegenRinne2 = open(ReadPipe,O_RDWR | O_NONBLOCK);
   		 usleep(INTERVALL);
   		 letzerBefehl = BefehlEmpfangen(newsockfd);
   		 switch (letzerBefehl)
   		 {
   		 case 0xff://Daten Senden
   			 double d[5];
   			 d[0] = rand() * 420;									//Wolkenverdeckung
   			 d[1] = DatenEmpfangen(RegenRinne1,RegenRinne2);		//Regen
   			 d[2] = rand() * 324872.123;							//Windgeschwindigkeit
   			 d[3] = rand() * 123.45;								//Himmelshelligkeit
   			 d[4] = rand() * 0.00123;								//Himmelsqualität
   			 if (DatenSenden(newsockfd, d)==-1)
				goto connect;
   			 if(BefehlSenden(newsockfd, 0xff)==-1)//noch da
				goto connect;
   			 break;
   		 case 0xfe:
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
