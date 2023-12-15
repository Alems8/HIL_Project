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


const char		k_local_interface[]	= "169.254.210.95";
const char		k_default_mcast_group[]	= "239.255.42.99";
const int		k_default_port		= 1511;




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

int open_udp_multicast_socket(int port, const char* mcastGroup, bool_t blocking)
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
void Unpack(char* pData)
{
    // Checks for NatNet Version number. Used later in function. Packets may be different depending on NatNet version.
//    int major = NatNetVersion[0];
//    int minor = NatNetVersion[1];

    char *ptr = pData;
    int i, j;

    printf("Begin Packet\n-------\n");

    // First 2 Bytes is message ID
    int MessageID = 0;
    memcpy(&MessageID, ptr, 2); ptr += 2;
    printf("Message ID : %d\n", MessageID);

    // Second 2 Bytes is the size of the packet
    int nBytes = 0;
    memcpy(&nBytes, ptr, 2); ptr += 2;
    printf("Byte count : %d\n", nBytes);
    
    if(MessageID == 7)      // FRAME OF MOCAP DATA packet
    {
        // Next 4 Bytes is the frame number
        int frameNumber = 0; memcpy(&frameNumber, ptr, 4); ptr += 4;
        printf("Frame # : %d\n", frameNumber);
        
        // Next 4 Bytes is the number of data sets (markersets, rigidbodies, etc)
        int nMarkerSets = 0; memcpy(&nMarkerSets, ptr, 4); ptr += 4;
        printf("Marker Set Count : %d\n", nMarkerSets);

        // Loop through number of marker sets and get name and data
        for (i=0; i < nMarkerSets; i++)
        {    
            // Markerset name
            char szName[256];
            strcpy(szName, ptr);
            int nDataBytes = (int) strlen(szName) + 1;
            ptr += nDataBytes;
            printf("Model Name: %s\n", szName);

            // marker data
            int nMarkers = 0; memcpy(&nMarkers, ptr, 4); ptr += 4;
            printf("Marker Count : %d\n", nMarkers);

            for(j=0; j < nMarkers; j++)
            {
                float x = 0; memcpy(&x, ptr, 4); ptr += 4;
                float y = 0; memcpy(&y, ptr, 4); ptr += 4;
                float z = 0; memcpy(&z, ptr, 4); ptr += 4;
                printf("\tMarker %d : [x=%3.2f,y=%3.2f,z=%3.2f]\n",j,x,y,z);
            }
        }

        // Loop through unlabeled markers
        int nOtherMarkers = 0; memcpy(&nOtherMarkers, ptr, 4); ptr += 4;
        // OtherMarker list is Deprecated
        printf("Unidentified Marker Count : %d\n", nOtherMarkers);
        for(j=0; j < nOtherMarkers; j++)
        {
            float x = 0.0f; memcpy(&x, ptr, 4); ptr += 4;
            float y = 0.0f; memcpy(&y, ptr, 4); ptr += 4;
            float z = 0.0f; memcpy(&z, ptr, 4); ptr += 4;
            
            // Deprecated
            printf("\tMarker %d : pos = [%3.2f,%3.2f,%3.2f]\n",j,x,y,z);
        }
        
        // Loop through rigidbodies
        int nRigidBodies = 0;
        memcpy(&nRigidBodies, ptr, 4); ptr += 4;
        printf("Rigid Body Count : %d\n", nRigidBodies);
        for (j=0; j < nRigidBodies; j++)
        {
            // Rigid body position and orientation 
            int ID = 0; memcpy(&ID, ptr, 4); ptr += 4;
            float x = 0.0f; memcpy(&x, ptr, 4); ptr += 4;
            float y = 0.0f; memcpy(&y, ptr, 4); ptr += 4;
            float z = 0.0f; memcpy(&z, ptr, 4); ptr += 4;
            float qx = 0; memcpy(&qx, ptr, 4); ptr += 4;
            float qy = 0; memcpy(&qy, ptr, 4); ptr += 4;
            float qz = 0; memcpy(&qz, ptr, 4); ptr += 4;
            float qw = 0; memcpy(&qw, ptr, 4); ptr += 4;
            printf("ID : %d\n", ID);
            printf("pos: [%3.2f,%3.2f,%3.2f]\n", x,y,z);
            printf("ori: [%3.2f,%3.2f,%3.2f,%3.2f]\n", qx,qy,qz,qw);

            // NatNet version 2.0 and later
//            if(major >= 2)
//            {
                // Mean marker error
                float fError = 0.0f; memcpy(&fError, ptr, 4); ptr += 4;
                printf("Mean marker error: %3.2f\n", fError);
//            }

            // NatNet version 2.6 and later
//            if( ((major == 2)&&(minor >= 6)) || (major > 2) || (major == 0) ) 
//            {
                // params
                short params = 0; memcpy(&params, ptr, 2); ptr += 2;
//                int bTrackingValid = params & 0x01; // 0x01 : rigid body was successfully tracked in this frame
//            }
		
        } // Go to next rigid body


/*
        // Skeletons (NatNet version 2.1 and later)
        if( ((major == 2)&&(minor>0)) || (major>2))
        {
            int nSkeletons = 0;
            memcpy(&nSkeletons, ptr, 4); ptr += 4;
            printf("Skeleton Count : %d\n", nSkeletons);

            // Loop through skeletons
            for (int j=0; j < nSkeletons; j++)
            {
                // skeleton id
                int skeletonID = 0;
                memcpy(&skeletonID, ptr, 4); ptr += 4;

                // Number of rigid bodies (bones) in skeleton
                int nRigidBodies = 0;
                memcpy(&nRigidBodies, ptr, 4); ptr += 4;
                printf("Rigid Body Count : %d\n", nRigidBodies);

                // Loop through rigid bodies (bones) in skeleton
                for (int j=0; j < nRigidBodies; j++)
                {
                    // Rigid body position and orientation
                    int ID = 0; memcpy(&ID, ptr, 4); ptr += 4;
                    float x = 0.0f; memcpy(&x, ptr, 4); ptr += 4;
                    float y = 0.0f; memcpy(&y, ptr, 4); ptr += 4;
                    float z = 0.0f; memcpy(&z, ptr, 4); ptr += 4;
                    float qx = 0; memcpy(&qx, ptr, 4); ptr += 4;
                    float qy = 0; memcpy(&qy, ptr, 4); ptr += 4;
                    float qz = 0; memcpy(&qz, ptr, 4); ptr += 4;
                    float qw = 0; memcpy(&qw, ptr, 4); ptr += 4;
                    printf("ID : %d\n", ID);
                    printf("pos: [%3.2f,%3.2f,%3.2f]\n", x,y,z);
                    printf("ori: [%3.2f,%3.2f,%3.2f,%3.2f]\n", qx,qy,qz,qw);

                    // Mean marker error (NatNet version 2.0 and later)
                    if(major >= 2)
                    {
                        float fError = 0.0f; memcpy(&fError, ptr, 4); ptr += 4;
                        printf("Mean marker error: %3.2f\n", fError);
                    }

                    // Tracking flags (NatNet version 2.6 and later)
                    if( ((major == 2)&&(minor >= 6)) || (major > 2) || (major == 0) ) 
                    {
                        // params
                        short params = 0; memcpy(&params, ptr, 2); ptr += 2;
//                        int bTrackingValid = params & 0x01; // 0x01 : rigid body was successfully tracked in this frame
                    }

                } // next rigid body

            } // next skeleton
        }

        // labeled markers (NatNet version 2.3 and later)
        if( ((major == 2)&&(minor>=3)) || (major>2))
        {
            int nLabeledMarkers = 0;
            memcpy(&nLabeledMarkers, ptr, 4); ptr += 4;
            printf("Labeled Marker Count : %d\n", nLabeledMarkers);

            // Loop through labeled markers
            for (int j=0; j < nLabeledMarkers; j++)
            {
                // id
                // Marker ID Scheme:
                // Active Markers:
                //   ID = ActiveID, correlates to RB ActiveLabels list
                // Passive Markers: 
                //   If Asset with Legacy Labels
                //      AssetID     (Hi Word)
                //      MemberID    (Lo Word)
                //   Else
                //      PointCloud ID
                int ID = 0; memcpy(&ID, ptr, 4); ptr += 4;
                int modelID, markerID;
                DecodeMarkerID(ID, &modelID, &markerID);


                // x
                float x = 0.0f; memcpy(&x, ptr, 4); ptr += 4;
                // y
                float y = 0.0f; memcpy(&y, ptr, 4); ptr += 4;
                // z
                float z = 0.0f; memcpy(&z, ptr, 4); ptr += 4;
                // size
                float size = 0.0f; memcpy(&size, ptr, 4); ptr += 4;

                // NatNet version 2.6 and later
                if( ((major == 2)&&(minor >= 6)) || (major > 2) || (major == 0) ) 
                {
                    // marker params
                    short params = 0; memcpy(&params, ptr, 2); ptr += 2;
                    bool bOccluded = (params & 0x01) != 0;     // marker was not visible (occluded) in this frame
                    bool bPCSolved = (params & 0x02) != 0;     // position provided by point cloud solve
                    bool bModelSolved = (params & 0x04) != 0;  // position provided by model solve
                    if ((major >= 3) || (major == 0))
                    {
                        bool bHasModel = (params & 0x08) != 0;     // marker has an associated model
                        bool bUnlabeled = (params & 0x10) != 0;    // marker is an unlabeled marker
                        bool bActiveMarker = (params & 0x20) != 0; // marker is an active marker
                    }

                }

                // NatNet version 3.0 and later
                float residual = 0.0f;
                if ((major >= 3) || (major == 0))
                {
                    // Marker residual
                    memcpy(&residual, ptr, 4); ptr += 4;
                }

                printf("ID  : [MarkerID: %d] [ModelID: %d]\n", markerID, modelID);
                printf("pos : [%3.2f,%3.2f,%3.2f]\n", x,y,z);
                printf("size: [%3.2f]\n", size);
                printf("err:  [%3.2f]\n", residual);
            }
        }

        // Force Plate data (NatNet version 2.9 and later)
        if (((major == 2) && (minor >= 9)) || (major > 2))
        {
            int nForcePlates;
            memcpy(&nForcePlates, ptr, 4); ptr += 4;
            for (int iForcePlate = 0; iForcePlate < nForcePlates; iForcePlate++)
            {
                // ID
                int ID = 0; memcpy(&ID, ptr, 4); ptr += 4;
                printf("Force Plate : %d\n", ID);

                // Channel Count
                int nChannels = 0; memcpy(&nChannels, ptr, 4); ptr += 4;

                // Channel Data
                for (int i = 0; i < nChannels; i++)
                {
                    printf(" Channel %d : ", i);
                    int nFrames = 0; memcpy(&nFrames, ptr, 4); ptr += 4;
                    for (int j = 0; j < nFrames; j++)
                    {
                        float val = 0.0f;  memcpy(&val, ptr, 4); ptr += 4;
                        printf("%3.2f   ", val);
                    }
                    printf("\n");
                }
            }
        }

        // Device data (NatNet version 3.0 and later)
        if (((major == 2) && (minor >= 11)) || (major > 2))
        {
            int nDevices;
            memcpy(&nDevices, ptr, 4); ptr += 4;
            for (int iDevice = 0; iDevice < nDevices; iDevice++)
            {
                // ID
                int ID = 0; memcpy(&ID, ptr, 4); ptr += 4;
                printf("Device : %d\n", ID);

                // Channel Count
                int nChannels = 0; memcpy(&nChannels, ptr, 4); ptr += 4;

                // Channel Data
                for (int i = 0; i < nChannels; i++)
                {
                    printf(" Channel %d : ", i);
                    int nFrames = 0; memcpy(&nFrames, ptr, 4); ptr += 4;
                    for (int j = 0; j < nFrames; j++)
                    {
                        float val = 0.0f;  memcpy(&val, ptr, 4); ptr += 4;
                        printf("%3.2f   ", val);
                    }
                    printf("\n");
                }
            }
        }
 
        // software latency (removed in version 3.0)
        if ( major < 3 )
        {
            float softwareLatency = 0.0f; memcpy(&softwareLatency, ptr, 4); ptr += 4;
            printf("software latency : %3.3f\n", softwareLatency);
        }

        // timecode
        unsigned int timecode = 0;  memcpy(&timecode, ptr, 4);  ptr += 4;
        unsigned int timecodeSub = 0; memcpy(&timecodeSub, ptr, 4); ptr += 4;
        char szTimecode[128] = "";
        TimecodeStringify(timecode, timecodeSub, szTimecode, 128);

        // timestamp
        double timestamp = 0.0f;

        // NatNet version 2.7 and later - increased from single to double precision
        if( ((major == 2)&&(minor>=7)) || (major>2))
        {
            memcpy(&timestamp, ptr, 8); ptr += 8;
        }
        else
        {
            float fTemp = 0.0f;
            memcpy(&fTemp, ptr, 4); ptr += 4;
            timestamp = (double)fTemp;
        }
        printf("Timestamp : %3.3f\n", timestamp);

        // high res timestamps (version 3.0 and later)
        if ( (major >= 3) || (major == 0) )
        {
            uint64_t cameraMidExposureTimestamp = 0;
            memcpy( &cameraMidExposureTimestamp, ptr, 8 ); ptr += 8;
            printf( "Mid-exposure timestamp : %" PRIu64"\n", cameraMidExposureTimestamp );

            uint64_t cameraDataReceivedTimestamp = 0;
            memcpy( &cameraDataReceivedTimestamp, ptr, 8 ); ptr += 8;
            printf( "Camera data received timestamp : %" PRIu64"\n", cameraDataReceivedTimestamp );

            uint64_t transmitTimestamp = 0;
            memcpy( &transmitTimestamp, ptr, 8 ); ptr += 8;
            printf( "Transmit timestamp : %" PRIu64"\n", transmitTimestamp );
        }

        // frame params
        short params = 0;  memcpy(&params, ptr, 2); ptr += 2;
        bool bIsRecording = (params & 0x01) != 0;                  // 0x01 Motive is recording
        bool bTrackedModelsChanged = (params & 0x02) != 0;         // 0x02 Actively tracked model list has changed


        // end of data tag
        int eod = 0; memcpy(&eod, ptr, 4); ptr += 4;
        printf("End Packet\n-------------\n");
*/

    }

}



// receive_packet --

void receive_packet(char* buffer, int buffer_size)
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
		Unpack(buffer);
}

// main --

int main(int argc, char* argv[])
{
	char	packet_buffer[K_SOCK_MAX_PACKET_SIZE];

	printf("optitrack minimal self contained (sc) started.\n");

	printf("openning multicast socket.\n");
	
	open_udp_multicast_socket(k_default_port, k_default_mcast_group, e_true);

	while (1) {
		receive_packet(packet_buffer, K_SOCK_MAX_PACKET_SIZE);
	}

	if (g_mcast_address != NULL)
		free((void*)g_mcast_address);
}
