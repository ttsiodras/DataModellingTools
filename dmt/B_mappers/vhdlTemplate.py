# (C) Semantix Information Technologies.
#
# Semantix Information Technologies is licensing the code of the
# Data Modelling Tools (DMT) in the following dual-license mode:
#
# Commercial Developer License:
#       The DMT Commercial Developer License is the appropriate version
# to use for the development of proprietary and/or commercial software.
# This version is for developers/companies who do not want to share
# the source code they develop with others or otherwise comply with the
# terms of the GNU General Public License version 2.1.
#
# GNU GPL v. 2.1:
#       This version of DMT is the one to use for the development of
# non-commercial applications, when you are willing to comply
# with the terms of the GNU General Public License version 2.1.
#
# The features of the two licenses are summarized below:
#
#                       Commercial
#                       Developer               GPL
#                       License
#
# License cost          License fee charged     No license fee
#
# Must provide source
# code changes to DMT   No, modifications can   Yes, all source code
#                       be closed               must be provided back
#
# Can create            Yes, that is,           No, applications are subject
# proprietary           no source code needs    to the GPL and all source code
# applications          to be disclosed         must be made available
#
# Support               Yes, 12 months of       No, but available separately
#                       premium technical       for purchase
#                       support
#
# Charge for Runtimes   None                    None
#
vhd = '''library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

--  Uncomment the following lines to use the declarations that are
--  provided for instantiating Xilinx primitive components.
--library UNISIM;
--use UNISIM.VComponents.all;

entity TASTE is
    port (
        USB_StreamCLK : in std_logic;
        USB_StreamFIFOADDR : out std_logic_vector(1 downto 0);
        USB_StreamPKTEND_n : out std_logic;
        USB_StreamFlags_n : in std_logic_vector(2 downto 0);
        USB_StreamSLOE_n : out std_logic;
        USB_StreamSLRD_n : out std_logic;
        USB_StreamSLWR_n : out std_logic;
        USB_StreamData : inout std_logic_vector(15 downto 0);
        USB_StreamFX2Rdy : in std_logic;

        USB_RegCLK : in std_logic;
        USB_RegAddr : in std_logic_vector(15 downto 0);
        USB_RegData : inout std_logic_vector(7 downto 0);
        USB_RegOE_n : in std_logic;
        USB_RegRD_n : in std_logic;
        USB_RegWR_n : in std_logic;
        USB_RegCS_n : in std_logic;

        USB_Interrupt : out std_logic;

        User_Signals : inout std_logic_vector(7 downto 0);

        S_CLK : out std_logic;
        S_A : out std_logic_vector(22 downto 0);
        S_DA : inout std_logic_vector(8 downto 0);
        S_DB : inout std_logic_vector(8 downto 0);
        S_ADV_LD_N : out std_logic;
        S_BWA_N : out std_logic;
        S_BWB_N : out std_logic;
        S_OE_N : out std_logic;
        S_WE_N : out std_logic;

        IO_CLK_N : inout std_logic;
        IO_CLK_P : inout std_logic;
        IO : inout std_logic_vector(46 downto 0)
    );
end TASTE;

architecture arch of TASTE is

    -- Declare interfaces component
    component ZestSC1_Interfaces
        port (
            -- FPGA pin connections
            USB_StreamCLK : in std_logic;
            USB_StreamFIFOADDR : out std_logic_vector(1 downto 0);
            USB_StreamPKTEND_n : out std_logic;
            USB_StreamFlags_n : in std_logic_vector(2 downto 0);
            USB_StreamSLOE_n : out std_logic;
            USB_StreamSLRD_n : out std_logic;
            USB_StreamSLWR_n : out std_logic;
            USB_StreamData : inout std_logic_vector(15 downto 0);
            USB_StreamFX2Rdy : in std_logic;

            USB_RegCLK : in std_logic;
            USB_RegAddr : in std_logic_vector(15 downto 0);
            USB_RegData : inout std_logic_vector(7 downto 0);
            USB_RegOE_n : in std_logic;
            USB_RegRD_n : in std_logic;
            USB_RegWR_n : in std_logic;
            USB_RegCS_n : in std_logic;

            USB_Interrupt : out std_logic;

            S_CLK: out std_logic;
            S_A: out std_logic_vector(22 downto 0);
            S_ADV_LD_N: out std_logic;
            S_BWA_N: out std_logic;
            S_BWB_N: out std_logic;
            S_DA: inout std_logic_vector(8 downto 0);
            S_DB: inout std_logic_vector(8 downto 0);
            S_OE_N: out std_logic;
            S_WE_N: out std_logic;

            -- User connections
            -- Streaming interface
            User_CLK : out std_logic;
            User_RST : out std_logic;

            User_StreamBusGrantLength : in std_logic_vector(11 downto 0);

            User_StreamDataIn : out std_logic_vector(15 downto 0);
            User_StreamDataInWE : out std_logic;
            User_StreamDataInBusy : in std_logic;

            User_StreamDataOut : in std_logic_vector(15 downto 0);
            User_StreamDataOutWE : in std_logic;
            User_StreamDataOutBusy : out std_logic;

            -- Register interface
            User_RegAddr : out std_logic_vector(15 downto 0);
            User_RegDataIn : out std_logic_vector(7 downto 0);
            User_RegDataOut : in std_logic_vector(7 downto 0);
            User_RegWE : out std_logic;
            User_RegRE : out std_logic;

            -- Signals and interrupts
            User_Interrupt : in std_logic;

            -- SRAM interface
            User_SRAM_A: in std_logic_vector(22 downto 0);
            User_SRAM_W: in std_logic;
            User_SRAM_R: in std_logic;
            User_SRAM_DR_VALID: out std_logic;
            User_SRAM_DW: in std_logic_vector(17 downto 0);
            User_SRAM_DR: out std_logic_vector(17 downto 0)
        );
    end component;

    -- Circuits for the existing PIs
%(circuits)s
    -- Declare signals
    signal CLK : std_logic;
    signal RST : std_logic;

    -- To report that circuit is running, use a counter to divide the clock
    -- and shift one bit thru the LEDs...
    signal LEDs : std_logic_vector(7 downto 0);
    signal LEDVal : std_logic_vector(7 downto 0);
    signal Count : std_logic_vector(21 downto 0);
    signal Dir : std_logic := '0';

    -- Register interface
    signal Addr : std_logic_vector(15 downto 0);
    signal DataIn : std_logic_vector(7 downto 0);
    signal DataOut : std_logic_vector(7 downto 0);
    signal WE : std_logic;
    signal RE : std_logic;

    -- Registers for I/O
%(ioregisters)s

    -- Signals for start/finish
%(startStopSignals)s

begin
    -- Tie unused signals
    --LEDs <= "11111111";
    IO_CLK_N <= 'Z';
    IO_CLK_P <= 'Z';
    IO <= (0=>LEDs(0), 1=>LEDs(1), 41=>LEDs(2), 42=>LEDs(3), 43=>LEDs(4),
           44=>LEDs(5), 45=>LEDs(6), 46=>LEDs(7), others => 'Z');

    LEDs <= not LEDVal;

    ---------------------------------------------------
    -- Indicate that FPGA is alive, by KIT-ing the LEDs
    ---------------------------------------------------

    process (CLK, RST)
    begin
        if (RST='1') then
            Count <= (others=>'0');
        elsif (CLK'event and CLK='1') then
            Count <= Count + 1;
        end if;
    end process;

    process (CLK, RST)
    begin
        if (RST='1') then
            Dir <= '0';
            LEDVal <= "00000001";
        elsif (CLK'event and CLK='1') then
            if (Count="0000000000000000000000") then
                if (Dir='0') then
                    LEDVal <= LEDVal(6 downto 0) & "0";
                    if (LEDVal="01000000") then
                        Dir <= '1';
                    end if;
                else
                    LEDVal <= "0" & LEDVal(7 downto 1);
                    if (LEDVal="00000010") then
                        Dir <= '0';
                    end if;
                end if;
            end if;
        end if;
    end process;

    -- Implement register write
    -- Note that for compatibility with FX2LP devices only addresses
    -- above 2000 Hex are used
    process (RST, CLK)
    begin
        if (RST='1') then
            -- Signals for reset
%(reset)s
        elsif (CLK'event and CLK='1') then

            -- Update start-stop pulses
%(updateStartStopPulses)s
            if (WE='1') then
                case Addr is
                      -- Read data from the USB bus
%(readinputdata)s
                 end case;
            end if;
        end if;
    end process;

    -- Implement register read
    --process (Addr, RE, gcd_Value3, gcd_CalculationsComplete)
    process (Addr, RE, %(outputs)s %(completions)s)
    begin
        if (RE='1') then
            case Addr is
                -- Write data to the USB bus
%(writeoutputdata)s
                when others => DataOut <= X"00";
            end case;
        else
            -- avoid latches
            DataOut <= X"00";
        end if;
    end process;

    -- Instantiate interfaces component
    Interfaces : ZestSC1_Interfaces
        port map (
            USB_StreamCLK => USB_StreamCLK,
            USB_StreamFIFOADDR => USB_StreamFIFOADDR,
            USB_StreamPKTEND_n => USB_StreamPKTEND_n,
            USB_StreamFlags_n => USB_StreamFlags_n,
            USB_StreamSLOE_n => USB_StreamSLOE_n,
            USB_StreamSLRD_n => USB_StreamSLRD_n,
            USB_StreamSLWR_n => USB_StreamSLWR_n,
            USB_StreamData => USB_StreamData,
            USB_StreamFX2Rdy => USB_StreamFX2Rdy,

            USB_RegCLK => USB_RegCLK,
            USB_RegAddr => USB_RegAddr,
            USB_RegData => USB_RegData,
            USB_RegOE_n => USB_RegOE_n,
            USB_RegRD_n => USB_RegRD_n,
            USB_RegWR_n => USB_RegWR_n,
            USB_RegCS_n => USB_RegCS_n,

            USB_Interrupt => USB_Interrupt,

            S_CLK => S_CLK,
            S_A => S_A,
            S_ADV_LD_N => S_ADV_LD_N,
            S_BWA_N => S_BWA_N,
            S_BWB_N => S_BWB_N,
            S_DA => S_DA,
            S_DB => S_DB,
            S_OE_N => S_OE_N,
            S_WE_N => S_WE_N,

            -- User connections
            -- Streaming interface
            User_CLK => CLK,
            User_RST => RST,

            User_StreamBusGrantLength => X"002",

            User_StreamDataIn => open,
            User_StreamDataInWE => open,
            User_StreamDataInBusy => '1',

            User_StreamDataOut => "0000000000000000",
            User_StreamDataOutWE => '0',
            User_StreamDataOutBusy => open,

            -- Register interface
            User_RegAddr => Addr,
            User_RegDataIn => DataIn,
            User_RegDataOut => DataOut,
            User_RegWE => WE,
            User_RegRE => RE,

            -- Interrupts
            User_Interrupt => '0',

            -- SRAM interface
            User_SRAM_A => "00000000000000000000000",
            User_SRAM_W => '0',
            User_SRAM_R => '0',
            User_SRAM_DR_VALID => open,
            User_SRAM_DW => "000000000000000000",
            User_SRAM_DR => open
        );

    -- Connections to the VHDL circuits
%(connectionsToSystemC)s

end arch;'''

makefile = r'''SYSTEMC_SRC=                    \\
    circuit.h                   \\
    circuit.cpp

SYSTEMC_GENERATED=              \\
%(circuit_autofiles)s

SRCS=\\
    TASTE.vhd           \\
    craft_gatelibrary.vhd       \\
    $(SYSTEMC_GENERATED)

all:    taste.bit

taste.bit:      $(SRCS)
%(tab)s#-git commit -m "`date`" -a
%(tab)smkdir -p "xst/projnav.tmp" || exit 1
%(tab)sxst -ise TASTE.ise -intstyle ise -ifn TASTE.xst -ofn TASTE.syr || exit 1
%(tab)sngdbuild.exe -ise TASTE.ise -intstyle ise -dd _ngo -aul -nt timestamp -uc ZestSC1.ucf -p xc3s1000-ft256-5 TASTE.ngc TASTE.ngd|| exit 1
%(tab)smap -ise "TASTE.ise" -intstyle ise -p xc3s1000-ft256-5 -cm area -ir off -pr b -c 100 -o TASTE_map.ncd TASTE.ngd TASTE.pcf || exit 1
%(tab)spar -ise "TASTE.ise" -w -intstyle ise -ol std -t 1 TASTE_map.ncd TASTE.ncd TASTE.pcf || exit 1
%(tab)strce -ise TASTE.ise -intstyle ise -e 3 -s 5 -xml TASTE.twx TASTE.ncd -o TASTE.twr TASTE.pcf || exit 1
%(tab)sbitgen -ise "TASTE.ise" -intstyle ise -f TASTE.ut TASTE.ncd || exit 1
%(tab)scp "$@" ../TASTE.bit || exit 1

$(SYSTEMC_GENERATED):   $(SYSTEMC_SRC)
%(tab)sfor i in $^ ; do if [ "`basename "$$i" | sed 's,^.*\.,,'`" = "cpp" ] ; then /c/Program\ Files/SystemCrafter/SystemCrafter\ SC/bin/craft.exe /vhdl $$i || exit 1; fi ; done

test:
%(tab)scd .. ;  ./TASTE.exe

%%.clean:
%(tab)s-rm -f $*.stx $*.ucf.untf $*.mrp $*.nc1 $*.ngm $*.prm $*.lfp
%(tab)s-rm -f $*.placed_ncd_tracker $*.routed_ncd_tracker
%(tab)s-rm -f $*.pad_txt $*.twx *.log *.vhd~ $*.dhp $*.jhd $*.cel
%(tab)s-rm -f $*.ngr $*.ngc $*.ngd $*.syr $*.bld $*.pcf
%(tab)s-rm -f $*_map.map $*_map.mrp $*_map.ncd $*_map.ngm $*.ncd $*.pad
%(tab)s-rm -f $*.par $*.xpi $*_pad.csv $*_pad.txt $*.drc $*.bgn
%(tab)s-rm -f $*.xml $*_build.xml $*.rpt $*.gyd $*.mfd $*.pnx $*.ise
%(tab)s-rm -f $*.vm6 $*.jed $*.err $*.ER result.txt tmperr.err *.bak *.vhd~
%(tab)s-rm -f impactcmd.txt
%(tab)s-rm -f $*.twr $*_usage.xml
%(tab)s-rm -f $*.bit $*.svf $*.exo $*.mcs $*.ptwx $*.unroutes
%(tab)s-rm -f *_log *stx *summary.html *summary.xml
%(tab)s-rm -f $*_map.xrpt $*_ngdbuild.xrpt $*_par.xrpt $*_xst.xrpt
%(tab)s-rm -f *fdo *.xmsgs *.bld *.ngc *.ngd *.ncd
%(tab)s-rm -f *.bit *.mcs *.exo *.pcf *.twr
%(tab)s-rm -rf _ngo xst $*_xdb
%(tab)s-rm -f $(SYSTEMC_GENERATED)
%(tab)s-rm -f ../TASTE.bit

clean:  TASTE.clean
'''

prj = '''vhdl work "craft_gatelibrary.vhd"
vhdl work "ZestSC1_SRAM.vhd"
vhdl work "ZestSC1_Host.vhd"
vhdl work "ZestSC1_Interfaces.vhd"
%(circuits)s
vhdl work "TASTE.vhd"
'''

per_circuit_vhd = """

--  Uncomment the following lines to use the declarations that are
--  provided for instantiating Xilinx primitive components.
--library UNISIM;
--use UNISIM.VComponents.all;

%(declaration)s

architecture arch of %(pi)s is

    -- Declare signals
    signal CLK : std_logic;
    signal RST : std_logic;

    type state_type is (
        wait_for_start_signal,
        signal_received,
        work_done
    );
    signal state : state_type := wait_for_start_signal;
begin

    CLK <= clock_%(pi)s;
    RST <= reset_%(pi)s;

    -- Possible clock divider
    process(CLK, RST)
    begin
        if (RST='1') then
            finish_%(pi)s <= '1';
        elsif (CLK'event and CLK='1') then
            case state is
                when wait_for_start_signal =>
                    if start_%(pi)s = '1' then
                        state <= signal_received;
                        finish_%(pi)s <= '0';
                    else
                        state <= wait_for_start_signal;
                    end if;
                when signal_received =>

                    -----------------------------
                    -- Do your processing here --
                    -----------------------------

                    state <= work_done;
                when work_done =>
                    finish_%(pi)s <= '1';
                    state <= wait_for_start_signal;
            end case;
        end if;
    end process;

end arch;
"""
