#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <cstdio>
#include <unistd.h>
#include "JSFDefs.h"
#include "InterfaceMessages.h"

#

#define PORT 1901 //porta de dados
#define BUFFER_SIZE 1024

void receiveFile(const char *filename)
{
    SonarMessageHeaderType hdr; /* Basic 16-byte message header */
    JSFDataType jsfData;        /* Data message structure */
    int sockfd;
    struct sockaddr_in server_addr;
    FILE *file;
    char buffer[sizeof(SonarMessageHeaderType)]; //Crio o buffer para receber o header
    int i = 0; //Variável para auxiliar na parada de loop
    //long file_size = 0; //Variável para armazenar o tamanho do arquivo


    // Cria o socket TCP
    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("Erro ao criar o socket");
        return;
    }

    // Configura o endereço do servidor
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = inet_addr("192.168.15.14");
    server_addr.sin_port = htons(PORT);

    // Conecta ao servidor
    if (connect(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Erro ao conectar ao servidor");
        close(sockfd);
        return;
    }

    // Abre o arquivo para escrita
    file = fopen(filename, "wb+"); //botei opção de escrever por cima se tiver, qq coisa mudar
    if (file == NULL) {
        perror("Erro ao abrir o arquivo para escrita");
        close(sockfd);
        return;
    }

    // Recebe os dados e escreve no arquivo
    while (1) {
        ssize_t bytesRead = recv(sockfd, buffer, sizeof(SonarMessageHeaderType), 0);
        if (bytesRead <= 0) {
            if (bytesRead == 0) {
                // A conexão foi fechada pelo lado remoto
                printf("A conexão foi fechada pelo lado remoto.\n");
            } else {
                // Ocorreu um erro durante a recepção dos dados
                perror("Erro ao receber dados");
                // Trate o erro de acordo com a sua lógica
            }
            continue; // Volta ao início do loop para aguardar novos dados
        }
        
        // Copia os dados do buffer para a estrutura
        memcpy(&hdr, buffer, sizeof(hdr)); //Coloca o recebido pelo buffer dentro da esrutura hdr


        if (hdr.startOfMessage != SONAR_MESSAGE_HEADER_START) //Verifica se aqui está o começo da mensagem
        {
            printf("MSG INVALIDA\n"); //Tratativa para esperar até receber uma mensagem com header válido
            continue;
        }

        //Tenho que escrever só de msgs válidas, então preciso checar
        //if (hdr.sonarMessage == SONAR_MESSAGE_DATA){
        fwrite(&hdr, sizeof(hdr), 1, file); //Escreve o cabeçalho da mensagem
        //}
        
        //file_size += sizeof(hdr)+hdr.byteCount; //Incrementa o tamanho do arquivo até a próxima msg

        switch (hdr.sonarMessage)
        {
            case SONAR_MESSAGE_DATA:
                {
                char buffer_3[sizeof(JSFDataType)]; //Mudo o buffer para receber a mensagem de dados
                ssize_t bytesRead_3 = recv(sockfd, buffer_3, sizeof(JSFDataType), 0); // Faz a leitura do cabeçalho da mensagem de dados - 240 bytes
                memcpy(&jsfData, buffer_3, sizeof(jsfData)); //Copio os dados para a estrutura jsfData
                fwrite(&jsfData, sizeof(JSFDataType), 1, file); //Escreve o cabeçalho da mensagem de dados no arquivo
                
                printf("Ping num %d\n", jsfData.pingNum);
                // Print contents of SONAR_MESSAGE_DATA

                size_t bufferSize = hdr.byteCount-sizeof(jsfData); //Define o tamanho do buffer de dados

                int16_t data[bufferSize / 2]; //Define os dados a serem recebidos como um array de inteiros de 16 bits, divido por 2 pois o byteCount é o tamanho em bytes e o int16_t é de 2 bytes
                
                char buffer_2[bufferSize]; //Crio um buffer com o tamanho de dados a serem recebidos

                ssize_t bytesRead_2 = recv(sockfd, buffer_2, bufferSize, 0); //buffer a ser recebido de dados

                memcpy(data, buffer_2, bufferSize); //Coloco os dados do buffer dentro do array data

                fwrite(&data, hdr.byteCount-sizeof(jsfData), 1, file); //Escrevo a mensagem de dados no arquivo
                
                printf("Tamanho do array data: %ld\n", sizeof(data));


                //Retiro sizeof(jsfData) pois a msg tem um cabeçalho no começo
                //if (fread(&data, sizeof(data), 1, fid) != 1) // Faz a leitura dos dados da mensagem de dados
                //    break;
                
                /*for (i = 0; i < (hdr.byteCount-sizeof(jsfData)); i+=2) // Incrementa o índice de 2 em 2 para ler pares de bytes
                {

                    uint8_t byte1 = getc(fid); // Lê o primeiro byte
                    uint8_t byte2 = getc(fid); // Lê o segundo byte

                    if (byte1 == EOF || byte2 == EOF) // Verifica se algum byte atingiu o final do arquivo
                        {
                            printf("Invalid file format\n");
                            break;
                        }
                    
                    int16_t value = (byte2 << 8) | byte1; // Combina os dois bytes em um valor de 16 bits

                    data[i / 2] = value; // Armazena o valor no array 'data'
                }*/

                //if (fread(&jsfData, sizeof(jsfData), 1, fid) != 1) // Faz a leitura do cabeçalho da mensagem de dados - 240 bytes
                //    break;

                // Processar o array 'data' conforme necessário
                // ...
                printf("Final de processamento\n");

                break;
                }
            default: //Caso não tenha pego nenhum tipo de mensagem avança para a próxima mensagem header
                
                size_t bufferSize_4 = hdr.byteCount; //Define o tamanho do buffer de dados

                char buffer_4[bufferSize_4]; //Crio um buffer com o tamanho de dados a serem recebidos

                ssize_t bytesRead_4 = recv(sockfd, buffer_4, bufferSize_4, 0);

                fwrite(&buffer_4, sizeof(buffer_4), 1, file); //Escreve a mensagem de dados no arquivo

                // Mover o ponteiro de leitura hdr.byteCount bytes à frente
                /*if (fseek(fid, hdr.byteCount, SEEK_CUR) != 0) {
                    printf("Invalid file format\n");
                    break;
                }*/
        }
        
        //if (i++ == 500) { //Para o loop após 100 msgs
        //    break;}
        
    }

    // Fecha o arquivo e o socket
    printf("Posição no arquivo -> %ld\n",ftell(file)); //Imprime a posição do ponteiro dentro do arquivo
    fclose(file);
    close(sockfd);

    printf("Arquivo recebido com sucesso.\n");
}

int main() {
    const char *filename = "sonar_file.jsf";
    receiveFile(filename);
    return 0;
}