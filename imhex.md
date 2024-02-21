# Imhex pattern;

Some patterns for use with [ImHex](https://github.com/WerWolv/ImHex).

## IntelTHCBase frame
For the raw data frames from thcbase;
```
#define IPTS_DFT_NUM_COMPONENTS 9
#define i16 s16
#define i8 s8

struct ipts_hid_frame {
	u32 size;
	u8 reserved1;
	u8 type;
	u8 reserved2;
};


struct  ipts_report {
	u8 type;
	u8 flags;
	u16 size;
};


u8 IPTS_DFT_ID_POSITION = 6;
u8 IPTS_DFT_ID_POSITION2 = 7;
u8 IPTS_DFT_ID_BUTTON   = 9;
u8 IPTS_DFT_ID_PRESSURE = 11;

struct ipts_pen_dft_window_row {
	u32 frequency;
	u32 magnitude;
	i16 real[IPTS_DFT_NUM_COMPONENTS]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
	i16 imag[IPTS_DFT_NUM_COMPONENTS]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
	i8 first;
	i8 last;
	i8 mid;
	i8 zero;
};

struct ipts_pen_dft_window {
	u32 timestamp; // counting at approx 8MHz
	u8 num_rows;
	u8 seq_num;
	u8 reserved[3]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
	u8 data_type;
	u8 reserved2[2]; // NOLINT(modernize-avoid-c-arrays,cppcoreguidelines-avoid-c-arrays)
	ipts_pen_dft_window_row x[num_rows];
		ipts_pen_dft_window_row y[num_rows];
};


struct combined {
    ipts_report header;
    
      match (header.type, header.size) {
        (0x5c, _): ipts_pen_dft_window window;
        (0xff, _): u32 end;
        (_, _): u8 data[header.size];
      }    
};


struct overarching {
 u32 outer_size;
 u8 pad[3];
 u32 inner_size;
 u8 pad2[7];
 //u8 data[inner_size - 4];
 combined d[12];
};

overarching base @ 0x03;
```


Second section in the data, usually beyond `0x6d0` or there about is 'bad' memory from the previous packets.


## DataSel & Dft
```

#define IPTS_DFT_NUM_COMPONENTS 9
#define i16 s16
#define i8 s8
#pragma pattern_limit 200000

/*
    IPTS_DFT_ID_POSITION = 6
    IPTS_DFT_ID_POSITION2 = 7
    IPTS_DFT_ID_BUTTON   = 9
    IPTS_DFT_ID_PRESSURE = 11
    IPTS_DFT_ID_10 = 10
    IPTS_DFT_ID_8 = 8
*/

struct datasel_end {
    u32 something[2];
    u8 indices[8];
    u8 _pad;
    u8 dft_type;
    u8 _01;
    u8 _ff;
};

struct datasel_allmag {
    u32 mag_x[16];  // at least, for dft type 0x0a; 10
    u32 mag_y[16];  // at least, for dft type 0x0a; 10
    datasel_end info;
};

struct datasel_something_and_mag{
    u32 u0;
    u32 u1;
    u32 mag;
};
struct datasel_0x08 {
    datasel_something_and_mag d_x[2];
    u32 mags_x[10];
    datasel_something_and_mag d_y[2];
    u32 mags_y[10];
    datasel_end info;
};

struct datasel_pos_dim{
    u32 something[6];
    u32 mag_x0;
    u32 something2[2];
    u32 mag_x1[7];

};

struct datasel_0x06 {
  datasel_pos_dim x;
  datasel_pos_dim y;
  datasel_end info;
};


struct datasel_unknown {
   u32 v[32];
    datasel_end info;
};

struct datasel_outer<T>{
    T [[inline]];
    u8 pad[148 - sizeof(T)] [[hidden, color("FF0000")]];
};


struct ipts_pen_dft_window_row {
	u32 frequency;
	u32 magnitude;
	i16 real[IPTS_DFT_NUM_COMPONENTS]  [[hidden]];
	i16 imag[IPTS_DFT_NUM_COMPONENTS]  [[hidden]];
	i8 first;
	i8 last;
	i8 mid;
	i8 zero  [[hidden]];
};

struct ipts_pen_dft_window {
	u32 timestamp; // counting at approx 8MHz
	u8 num_rows;
	u8 seq_num;
	u8 reserved[3]  [[hidden]];
	u8 data_type;
	u8 reserved2[2]  [[hidden]];
	ipts_pen_dft_window_row x[num_rows];
		ipts_pen_dft_window_row y[num_rows];
};

struct combined {
    u8 pad[148] [[hidden]];
    
    ipts_pen_dft_window dft;
    
      match (dft.data_type) {
        (0x06): datasel_outer<datasel_0x06> data @ addressof(pad);
        (0x07): datasel_outer<datasel_allmag> data @ addressof(pad);
        (0x0a): datasel_outer<datasel_allmag> data @ addressof(pad);
        (0x0b): datasel_outer<datasel_allmag> data @ addressof(pad);
        (0x08): datasel_outer<datasel_0x08> data @ addressof(pad);
        (_): datasel_outer<datasel_unknown> data @ addressof(pad);
      }   
    
    u8 pad2[2000 - sizeof(pad) - sizeof(dft)] [[hidden]];
};

combined all[300] @ 0x0;


```
