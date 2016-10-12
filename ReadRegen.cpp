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
#include <iostream>

using namespace std;

  
int main(int argc, char *argv[])
{
  int fd, n, i, pipe;
  char buf[6];
  struct termios toptions;
  const char * RegenRinne = "/tmp/RegenRinne";
  double Rain;
  int rect;
  
  mkfifo(RegenRinne, 0666);
  pipe = open(RegenRinne, O_WRONLY);

  /* open serial port */
  fd = open("/dev/ttyUSB0", O_RDWR | O_NOCTTY);
  printf("fd opened as %i\n", fd);
  
  /* get current serial port settings */
  tcgetattr(fd, &toptions);
  /* set 9600 baud both ways */
  cfsetispeed(&toptions, B9600);
  cfsetospeed(&toptions, B9600);
  /* 8 bits, no parity, no stop bits */
  toptions.c_cflag &= ~PARENB;
  toptions.c_cflag &= ~CSTOPB;
  toptions.c_cflag &= ~CSIZE;
  toptions.c_cflag |= CS8;
  /* Canonical mode */
  toptions.c_lflag |= ICANON;
  /* commit the serial port settings */
  tcsetattr(fd, TCSANOW, &toptions);

  /* Receive string from Arduino */
  do{
  n = read(fd, buf, 6);
  /* insert terminating zero in the string */
  buf[n] = 0;
  
  sscanf(buf, "%d", &rect);
  Rain = 1-(double)rect/1024.0;
  
  cout << rect << endl;
  cout << Rain << endl;
  
  
  write(pipe, (void *)&Rain, sizeof(Rain));
  
  
  
}while(1);
close(pipe);
close(fd);

  return 0;
}
