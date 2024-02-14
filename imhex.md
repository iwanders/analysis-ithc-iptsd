# Imhex pattern;

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