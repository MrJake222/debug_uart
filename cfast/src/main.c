#include <stdio.h>
#include <stdbool.h>

#include <fcntl.h>
#include <termios.h>
#include <unistd.h>
#include <sys/poll.h>

#include <cintelhex.h>
#include <time.h>

#define I_ADR_PTR_SET   0x01
#define I_ADR_PTR_GET   0x03
#define I_MEM_WR        0x04
#define I_MEM_RD        0x05
#define I_CPU_RUN_CYC   0x20
#define I_CPU_RESET     0x21
#define I_CPU_FREERUN   0x22
#define R_ACK           0x01

void app(uint8_t* arr, int* idx, uint8_t val) {
    arr[*idx] = val;
    (*idx)++;
}

int gen_bitstream(ihex_recordset_t* rs, uint8_t* req, int* req_len, bool write, uint8_t* rsp, int* rsp_len) {
    uint i = 0;
    ihex_record_t* rec;
    uint32_t off;
    int err;

    *req_len = 0;
    *rsp_len = 0;

    uint32_t last_addr = -1;
    while (1) {
        err = ihex_rs_iterate_data(rs, &i, &rec, &off);
        if (err) {
            printf("failed iterating hex");
            return 1;
        }
        if (!rec) {
            break;
        }

        uint32_t rec_addr = off + rec->ihr_address;
        if (last_addr != rec_addr) {
            printf("gen: setting adr_ptr = %x\n", rec_addr);

            app(req, req_len, I_ADR_PTR_SET);
            app(req, req_len, rec_addr);
            app(req, req_len, rec_addr >> 8);
            app(req, req_len, rec_addr >> 16);
            app(req, req_len, rec_addr >> 24);

            app(rsp, rsp_len, R_ACK);

            last_addr = rec_addr;
        }

        for (int j=0; j<rec->ihr_length; j+=4) {
            if (write) {
                app(req, req_len, I_MEM_WR);
                for (int k=0; k<4; k++)
                    app(req, req_len, rec->ihr_data[j+k]);

                app(rsp, rsp_len, R_ACK);
            }
            else {
                app(req, req_len, I_MEM_RD);

                for (int k=0; k<4; k++)
                    app(rsp, rsp_len, rec->ihr_data[j+k]);
            }

            last_addr += 4;
        }
    }

    printf("gen: bitstream %s length %d, expected response %d bytes\n",
           (write ? "write" : "read"), *req_len, *rsp_len);

    return 0;
}

int sport_setup(int fd, speed_t speed) {
    int r;
    struct termios tty;
    r = tcgetattr(fd, &tty);
    if (r < 0) {
        puts("tcgetattr");
        return 1;
    }

    tty.c_cflag &= ~PARENB;     // no parity
    tty.c_cflag &= ~CSTOPB;     // stop 1
    tty.c_cflag &= ~CSIZE;      // clr transfer bits
    tty.c_cflag |= CS8;         // 8 bits per transfer
    tty.c_cflag &= ~CRTSCTS;    // no flow control
    tty.c_cflag |= CREAD | CLOCAL; // disable ctrl lines
    tty.c_lflag &= ~ICANON;     // no line-by-line mode
    tty.c_lflag &= ~ECHO;       // no echo
    tty.c_lflag &= ~ECHOE;      // no erasure
    tty.c_lflag &= ~ECHONL;     // no new-line echo
    tty.c_lflag &= ~ISIG;       // no signal chars

    tty.c_iflag &= ~(IXON | IXOFF | IXANY); // no sw flow control
    // disable special handling
    tty.c_iflag &= ~(IGNBRK|BRKINT|PARMRK|ISTRIP|INLCR|IGNCR|ICRNL);
    tty.c_oflag &= ~OPOST; // no special interpretation of output bytes (e.g. newline chars)
    tty.c_oflag &= ~ONLCR; // no conversion of newline to carriage return/line feed
    tty.c_cc[VMIN] = 0;    // minimum chars to receive
    tty.c_cc[VTIME] = 10;   // sec timeout * 10

    r = cfsetspeed(&tty, speed);
    if (r < 0) {
        puts("cfsetspeed");
        return 1;
    }

    r = tcsetattr(fd, TCSANOW, &tty);
    if (r < 0) {
        puts("tcsetattr");
        return 1;
    }

    return 0;
}

int sport_exchange(int fd, uint8_t* req, int req_len, uint8_t* rsp, int rsp_len) {
    struct pollfd pollfd = {
            .fd = fd,
            .events = POLLOUT | POLLIN
    };

    int r;
    long wi = 0;
    long ri = 0;

    do {
        r = poll(&pollfd, 1, 1000);
        if (r == 0) {
            printf("\ntimeout\n");
            return 1;
        }

        if (pollfd.revents & POLLOUT) {
            wi += write(pollfd.fd, req + wi, req_len - wi);

            if (wi == req_len)
                // all written, stop polling for writes
                pollfd.events &= ~POLLOUT;
        }

        if (pollfd.revents & POLLIN) {
            ri += read(pollfd.fd, rsp + ri, rsp_len - ri);
        }

        printf("\rwi=%5ld, ri=%5ld", wi, ri);
    }
    while (ri != rsp_len);

    printf("\n");
    return 0;
}

int compare(uint8_t* rsp, uint8_t* rsp_sport, int rsp_len) {
    bool good = true;
    for (int i=0; i<rsp_len; i++) {
        if (rsp[i] != rsp_sport[i]) {
            printf("response mismatch: first at byte %05x: is %02x, should be %02x\n", i, rsp_sport[i], rsp[i]);
            good = false;
            break;
        }
    }

    return good ? 0 : 1;
}

double delta_ms(struct timespec start, struct timespec end) {
    double ms =  (double)(end.tv_sec  - start.tv_sec ) * 1000;
           ms += (double)(end.tv_nsec - start.tv_nsec) / 1000000;

   return ms;
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        printf("Usage: %s [serial port] [hex file]\n", argv[0]);
        return 1;
    }

    const char* sport_path = argv[1];
    const char* ihex_path = argv[2];

    ihex_recordset_t* rs = ihex_rs_from_file(ihex_path);
    if (!rs) {
        printf("failed reading hex\n");
        return 2;
    }

    int r = 0;

    int fd = open(sport_path, O_RDWR);
    if (fd < 0) {
        perror("open");
        return 2;
    }
    r = sport_setup(fd, B1000000);
    if (r) {
        close(fd);
        return 2;
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC_RAW, &start);

    // write request
    // worst case write: adr_ptr update each record + 16 byte records (+4 instr)
    uint8_t* write_req = malloc((5+20) * rs->ihrs_count);

    // write response
    // worst case write: adr_ptr update each record (1) + 4x4 write ack
    uint8_t* write_rsp = malloc((1+4) * rs->ihrs_count);
    uint8_t* write_rsp_sport = malloc((1+4) * rs->ihrs_count);

    int write_req_len, write_rsp_len;
    gen_bitstream(rs, write_req, &write_req_len, true, write_rsp, &write_rsp_len);

    r = sport_exchange(fd, write_req, write_req_len, write_rsp_sport, write_rsp_len);
    if (r) {
        r = 3;
        goto write_end;
    }
    r = compare(write_rsp, write_rsp_sport, write_rsp_len);
    if (r) {
        r = 4;
        printf("write: response mismatch\n");
        goto write_end;
    }

    clock_gettime(CLOCK_MONOTONIC_RAW, &end);
    printf("write: ok %.2fs\n\n", delta_ms(start, end)/1000);
    
write_end:
    free(write_req);
    free(write_rsp);
    free(write_rsp_sport);
    
    if (r)
        return r;

    clock_gettime(CLOCK_MONOTONIC_RAW, &start);

    // read request
    // worst case read: adr_ptr update each record + 4 bytes read (4x4)
    uint8_t* read_req = malloc((5+4) * rs->ihrs_count);

    // read response
    // worst case read: adr_ptr update each record (1) + 4x4 bytes read
    uint8_t* read_rsp = malloc((1+16) * rs->ihrs_count);
    uint8_t* read_rsp_sport = malloc((1+16) * rs->ihrs_count);

    int read_req_len, read_rsp_len;
    gen_bitstream(rs, read_req, &read_req_len, false, read_rsp, &read_rsp_len);

    r = sport_exchange(fd, read_req, read_req_len, read_rsp_sport, read_rsp_len);
    if (r) {
        r = 5;
        goto read_end;
    }
    r = compare(read_rsp, read_rsp_sport, read_rsp_len);
    if (r) {
        r = 6;
        printf("read: response mismatch\n");
        goto read_end;
    }

    clock_gettime(CLOCK_MONOTONIC_RAW, &end);
    printf("read: ok %.2fs\n\n", delta_ms(start, end)/1000);
    
read_end:
    free(read_req);
    free(read_rsp);
    free(read_rsp_sport);

    if (r)
        return r;

    // restart & freerun enable
    uint8_t rf_req[] = { I_CPU_RESET, I_CPU_FREERUN, 0x01 };
    uint8_t rf_rsp[2] = { 0x01, 0x01 };
    uint8_t rf_rsp_sport[2];

    r = sport_exchange(fd, rf_req, sizeof(rf_req), rf_rsp_sport, sizeof(rf_rsp));
    if (r) {
        r = 7;
        goto rf_end;
    }
    r = compare(rf_rsp, rf_rsp_sport, sizeof(rf_rsp));
    if (r) {
        r = 8;
        printf("rf: response mismatch\n");
        goto rf_end;
    }

    printf("restart, freerun: ok\n\n");

rf_end:

    if (r)
        return r;

    return 0;
}
