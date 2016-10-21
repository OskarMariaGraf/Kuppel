#include <iostream>
#include <sstream>
#include <ctime>
#include <chrono>
#include "utility.h"
#include <string>
#include <cstring>

using namespace std;

string currentTime()
{
    time_t t = time(0);
    struct tm * ti = localtime(&t);
    stringstream output;
    output <<ti->tm_mday<<"."<<ti->tm_mon+1 << "." <<ti->tm_year + 1900 << " "<< ti->tm_hour<<":" << ti->tm_min<<":" << ti->tm_sec<< ": ";
    return output.str();
}
void error(string msg) {
    cout <<currentTime() << msg << ": " << strerror(errno)<< endl;
}
