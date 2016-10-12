//g++ -o Server Server.cpp

#define INTERVALL 1000000	//1s
#define READTIMEOUT 50		//0.5s

#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <iostream>
#include <unistd.h>
#include <sys/stat.h>//----------------
#include <fcntl.h> //-----------------

using namespace std;

int newsockfd = 0;
int austausch = 0;
int RegenRinne = 0;
const char* myfifo = "/tmp/RegenRinne";
double buf;

void CleanUp()
{
    if (newsockfd != 0)
   	 close(newsockfd);
}

void error(string msg) {
    cout << msg << ": " << strerror(errno)<< endl;
}

int DatenSenden(int sockfd, double Daten[5]) {
    int n;
    char *buffer = (char*)&Daten[0];
    if ((n = write(sockfd, buffer, 40)) < 0)
    {
   	 error("ERROR beim Senden der Daten");
   	 return -1;
    }
    cout << austausch <<": Daten gesendet" << endl;
return 1;
}

int BefehlSenden(int sockfd, char Befehl) {
    int n;
    if ((n = write(sockfd, (void *)&Befehl, 1)) < 0)
    {
   	 error("ERROR beim Senden eines Befehls");
   	 return -1;
    }
    cout << austausch<<": Befehl " << (int)Befehl << " gesendet" << endl;
return 1;
}

double DatenEmpfangen(int sockfd) {
    double buffer, buffer2 ;
    int n;
		n = read(sockfd, (void *)&buffer,8);
    if (n <= 0)
    {
   	 error("ERROR beim Empfangen der Sensordaten");
   	 return 420;
    }
    cout << austausch<<": SensorDaten " << (double)buffer << " empfangen" << endl;
    return buffer;
}

char BefehlEmpfangen(int sockfd) {
    char buffer;
    int n;
	n= read(sockfd, (void *)&buffer,1);
    if (n <= 0)
    {
   	 error("ERROR beim Empfangen des Befehls");
   	 return 0xfe;
    }
    cout << austausch<<": Befehl " << (int)buffer << " empfangen" << endl;
    return buffer;
}

int main(int argc, char *argv[]) {
    atexit(CleanUp);
    int sockfd, portno = 5902, clilen;
    char buffer[256];
    struct sockaddr_in serv_addr, cli_addr;
    int n;
    char letzerBefehl = 0;
    printf("Port #%d\n", portno);
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
   	 cout << "Warte auf Verbindung..." << endl;
   	 if ((newsockfd = accept(sockfd, (struct sockaddr *) &cli_addr, (socklen_t*)&clilen)) < 0)
   		 error("ERROR beim Annehmen der Verbindung");
	struct timeval timeout;      
    	timeout.tv_sec = READTIMEOUT;
    	timeout.tv_usec = 0;

    	if (setsockopt (newsockfd, SOL_SOCKET, SO_RCVTIMEO, (char *)&timeout,
                sizeof(timeout)) < 0)
        	error("setsockopt failed\n");

    	if (setsockopt (newsockfd, SOL_SOCKET, SO_SNDTIMEO, (char *)&timeout,
                sizeof(timeout)) < 0)
        	error("setsockopt failed\n");
   	 cout << "Client verbunden" << endl;
   	 while (1) {
		 RegenRinne = open(myfifo, O_RDONLY | O_NONBLOCK);	//RegenPipe
   		 usleep(INTERVALL);
		austausch++;
   		 letzerBefehl = BefehlEmpfangen(newsockfd);
   		 switch (letzerBefehl)
   		 {
   		 case 0xff://Daten Senden
   			 double d[5];
   			 d[0] = 420;									//Wolkenverdeckung
   			 d[1] = DatenEmpfangen(RegenRinne);				//Regen
   			 d[2] = 324872.123;								//Windgeschwindigkeit
   			 d[3] = 123.45;									//Himmelshelligkeit
   			 d[4] = 0.00123;								//Himmelsqualität
   			 if (DatenSenden(newsockfd, d)==-1)
				goto connect;
   			 if(BefehlSenden(newsockfd, 0xff)==-1)//noch da
				goto connect;
   			 break;
   		 case 0xfe:
   			 cout << "Client hat Verbindung beendet" << endl;
   			 goto connect;
   		 default:
   			 cout << "unbekannten Befehl erhalten" << endl;
   			 break;
   		 }
   	 }
    }
    return 0;
}
