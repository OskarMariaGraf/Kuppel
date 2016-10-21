//Copyright 1000% @ Christopher Wrobel //2000% @David Berger // unendlich% @Christopher Wrobel
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <fcntl.h>
#include <termios.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <iostream>


using namespace std;
  
int main(int argc, char *argv[])
{
  int fd, n, i, pipe1,pipe2;
  char buf[6];
  struct termios toptions;
  const char * RegenRinne1 = "/tmp/RegenRinne1";
  const char * RegenRinne2 = "/tmp/RegenRinne2";
  double Rain;
  int rect;
  char receive;
  
  mkfifo(RegenRinne1, 0666);
  mkfifo(RegenRinne2, 0666);
  pipe1 = open(RegenRinne1, O_RDWR);
  pipe2 = open(RegenRinne2, O_RDWR);
  /* Öffnen des Ports zum Arduino (Seriell) */
  fd = open("/dev/ttyUSB0", O_RDWR | O_NOCTTY);
  printf("fd opened as %i\n", fd);
  
  /* Abfragen der aktuellen Seriell-Port Einstellungen */
  tcgetattr(fd, &toptions);
  /* Baudrate 9600; Bidirektional */
  cfsetispeed(&toptions, B9600);
  cfsetospeed(&toptions, B9600);
  /* 8 bits, no parity, no stop bits */
  toptions.c_cflag &= ~PARENB;
  toptions.c_cflag &= ~CSTOPB;
  toptions.c_cflag &= ~CSIZE;
  toptions.c_cflag |= CS8;
  /* Canonical mode */
  toptions.c_lflag |= ICANON;
  /* Abschicken der Optionen */
  tcsetattr(fd, TCSANOW, &toptions);

  while(1){
	  
  read(pipe1,&receive,1); //Warten auf Anweisung vom Server Daten zu lesen
  write(fd, "A",1); //Daten abfragen
    n = read(fd, buf, 6);
  /* 0 als Abschluss zum String hinzufügen */
  buf[n] = 0;
  
  sscanf(buf, "%d", &rect); //Zusammenbauen der Empfangenen Daten
  Rain = 1-(double)rect/1024.0; //Umrechnen zu Prozent
  
  cout <<currentTime()<< rect << endl; //Debug Output
  cout <<currentTime()<< Rain << endl;
  
  write(pipe2, (void *)&Rain, sizeof(Rain)); //Übertragung zum Server
  
}
close(pipe1); // Schließen aller offenen Streams
close(pipe2);
close(fd);

  return 0;
}
