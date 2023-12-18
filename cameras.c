//
//  optitrack_minimal_sc.c
//  postwimp
//
//  Created by Francois Berard on 15/11/17.
//  Copyright (c)2017 LIG-IIHM. All rights reserved.
//
//	2021 01 25 FB
//		Added winsock initialization in "open_udp_multicast_socket", thx to Theo Recking

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef _WIN32
#include <unistd.h>
  #include <sys/socket.h>
  #include <sys/types.h>
  #include <sys/socket.h>
  #include <arpa/inet.h>
  #include <netinet/in.h>
  #include <fcntl.h>
#else
#include <winsock2.h>
#include <tchar.h>
#include <conio.h>
#include <ws2tcpip.h>
#endif


typedef enum {
    e_false		= 0,
    e_true		= 1
} bool_t;

int			g_mcast_socket		= -1;
void*			g_mcast_address		= NULL;
bool_t			g_blocking		= e_false;
#define			K_SOCK_MAX_PACKET_SIZE	20000


// open_udp_multicast_socket --
//
//	<port>			you should probably pass <k_default_port>.
//	<mcastGroup>		you should probably pass <k_default_mcast_group>.
//	<blocking>		e_true: read will block for next packet,
//				e_false: read will not block even if no packet has been received.

int open_udp_multicast_socket(int port, const char* mcastGroup, bool_t blocking, const char* k_local_interface)
{
    struct sockaddr_in*	si_me;
    struct ip_mreq		mreq;
    int			res;

#ifndef _WIN32
    in_addr_t		local_interface = htonl(INADDR_ANY);
#else
    ULONG			local_interface = inet_addr(k_local_interface);
    static int		winsock_initialized = 0;

    if (!winsock_initialized) {
        WORD		wVersionRequested;
        WSADATA		wsaData;
        int		err;

        /* Use the MAKEWORD(lowbyte,highbyte) macro declared in Windef.h */
        wVersionRequested = MAKEWORD(2,2);

        err = WSAStartup(wVersionRequested, &wsaData);
        if(err != 0) {
            /* Tell the user that we could not find a usable */
            /* Winsock DLL                                   */
            printf("WSAStartup failed with error: %d\n",err);
            return 1;
        }
        winsock_initialized	= 1;
    }
#endif
    if (g_mcast_socket != -1) {
        fprintf(stderr, "optitrack_t: multicast socket already opened\n");
        return 0;
    }

    if ((g_mcast_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0) {
        fprintf(stderr, "optitrack_t: Could not create UDP socket\n");
        goto failure;
    }

    // Save local address: we will use it to wake the listening thread by sending a packet.

    g_mcast_address		= malloc(sizeof(struct sockaddr_in));
    si_me			= (struct sockaddr_in*)g_mcast_address;
    memset((char*)si_me, 0, sizeof(*si_me));
    si_me->sin_family	= AF_INET;
    si_me->sin_port		= htons(port);
    si_me->sin_addr.s_addr	= local_interface;

    if (bind(g_mcast_socket, (struct sockaddr*)si_me, sizeof(*si_me)) < 0) {
        fprintf(stderr, "optitrack_t: Could not bind UDP socket to local address and port\n");
        goto failure;
    }

    mreq.imr_multiaddr.s_addr = inet_addr(mcastGroup);
    mreq.imr_interface.s_addr = local_interface;

#ifndef _WIN32
    if (setsockopt(g_mcast_socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq)) < 0)
#else
    if (setsockopt(g_mcast_socket, IPPROTO_IP, IP_ADD_MEMBERSHIP, (char*)&mreq, sizeof(mreq)) < 0)
#endif
    {
        fprintf(stderr, "optitrack_t: Could not join multicast group\n");
        goto failure;
    }

    g_blocking = blocking;
    if (!blocking) {
#ifndef _WIN32
        res = fcntl(g_mcast_socket, F_SETFL, O_NONBLOCK);
#else
        u_long iMode = 1;
        res = ioctlsocket(g_mcast_socket,FIONBIO,&iMode);
#endif
    }

    return 0;

    failure:
    if (g_mcast_socket != -1) {
#ifndef _WIN32
        close(g_mcast_socket);
#else
        closesocket(g_mcast_socket);
#endif
        g_mcast_socket = -1;
    }

    return 1;
}



// *********************************************************************
//
//  Unpack Data:
//      Recieves pointer to bytes that represent a packet of data
//
//      There are lots of print statements that show what
//      data is being stored
//
//      Most memcpy functions will assign the data to a variable.
//      Use this variable at your descretion.
//      Variables created for storing data do not exceed the
//      scope of this function.
//
// *********************************************************************
float* Unpack(char* pData, float* point)
{
    // Checks for NatNet Version number. Used later in function. Packets may be different depending on NatNet version.
//    int major = NatNetVersion[0];
//    int minor = NatNetVersion[1];

    char *ptr = pData;

    // First 2 Bytes is message ID
    int MessageID = 0;
    memcpy(&MessageID, ptr, 2); ptr += 12;
    // printf("Message ID : %d\n", MessageID);


    if(MessageID == 7)      // FRAME OF MOCAP DATA packet
    {
        // Loop through unlabeled markers
        int nOtherMarkers = 0; memcpy(&nOtherMarkers, ptr, 4); ptr += 4;
        // OtherMarker list is Deprecated

        if (nOtherMarkers == 0){
            point[0] = 0;
            point[1] = 0;
            point[2] = 0;
            return point;
        }

        // At least one point then acquire coordinates
        float x = 0.0f; memcpy(&x, ptr, 4); ptr += 4;
        float y = 0.0f; memcpy(&y, ptr, 4); ptr += 4;
        float z = 0.0f; memcpy(&z, ptr, 4); //No ptr update needed

        // Acquiring coordinates
        point[0] = x;
        point[1] = z;
        point[2] = (nOtherMarkers == 1) ? 1 : 0;

        /* In practice, for our interface work at most two points must be detected.
         * We clean up the room about other detectable objects a priori.  */
    }
    return point;

}

// receive_packet --

float* receive_packet(char* buffer, int buffer_size, float* point)
{
    int				nbytes;
    struct sockaddr_in		peer;
    socklen_t			slen				= sizeof(peer);

#ifndef _WIN32
    nbytes = recvfrom(g_mcast_socket, (void*)buffer, buffer_size, 0, (struct sockaddr*)&peer, &slen);
#else
    nbytes = recvfrom(g_mcast_socket, (char*)buffer, buffer_size, 0, (struct sockaddr*)&peer, &slen);
#endif

    if (nbytes > 0)
        return Unpack(buffer, point);
    return 0;
}

void start_connection(const char* k_local_interface){
    /* Function used to start up connection. change k_local_interface[] according to your interface */
    const char		k_default_mcast_group[]	= "239.255.42.99";
    const int		k_default_port		= 1511;

    printf("optitrack minimal self contained (sc) started.\n");
    printf("openning multicast socket.\n");
    open_udp_multicast_socket(k_default_port, k_default_mcast_group, e_true, k_local_interface);
}

void get_point(float* point) {
    char packet_buffer[K_SOCK_MAX_PACKET_SIZE];
    receive_packet(packet_buffer, K_SOCK_MAX_PACKET_SIZE, point);
}

int main(int argc, char* argv[]) {
    start_connection("169.254.210.95");
    while (1) {
        float points[3];  // Create an array to store the points
        get_point(points);
        printf("The point's coordinates are: x: %f, z: %f - Am I selecting the button? %f \n", points[0], points[1], points[2]);
    }
    return 0;
}
