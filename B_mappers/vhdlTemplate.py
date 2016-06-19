#
# (C) Semantix Information Technologies.
#
# Semantix Information Technologies is licensing the code of the
# Data Modelling Tools (DMT) in the following dual-license mode:
#
# Commercial Developer License:
#       The DMT Commercial Developer License is the suggested version
# to use for the development of proprietary and/or commercial software.
# This version is for developers/companies who do not want to comply
# with the terms of the GNU Lesser General Public License version 2.1.
#
# GNU LGPL v. 2.1:
#       This version of DMT is the one to use for the development of
# applications, when you are willing to comply with the terms of the
# GNU Lesser General Public License version 2.1.
#
# Note that in both cases, there are no charges (royalties) for the
# generated code.
#

# pylint: disable=anomalous-backslash-in-string

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

    -- Register interface
    signal Addr : std_logic_vector(15 downto 0);
    signal DataIn : std_logic_vector(7 downto 0);
    signal DataOut : std_logic_vector(7 downto 0);
    signal WE : std_logic;
    signal RE : std_logic;

    -- Registers for I/O
%(ioregisters)s
    signal Sig : std_logic_vector(3 downto 0);

    -- Signals for start/finish
%(startStopSignals)s
    -- Possible clock divider that drops frequency to 1/2, 1/4, 1/8, etc
    signal MyCLK : std_logic;

begin
    -- Tie unused signals
    --LEDs <= "11111111";
    IO_CLK_N <= 'Z';
    IO_CLK_P <= 'Z';
    IO <= (0=>LEDs(0), 1=>LEDs(1), 41=>LEDs(2), 42=>LEDs(3), 43=>LEDs(4),
           44=>LEDs(5), 45=>LEDs(6), 46=>LEDs(7), others => 'Z');

    -- Possible clock divider
    process(CLK, RST)
        variable InnerCount: Natural range 0 to 3;
    begin
        if (RST='1') then
            InnerCount := 0;
            MyCLK <= '0';
        elsif (CLK'event and CLK='1') then
            if InnerCount = 3 then
                InnerCount := 0;
            else
                InnerCount := InnerCount + 1;
            end if;
            if InnerCount >= 2 then
                MyCLK <= '0';
            else
                MyCLK <= '1';
            end if;
%(updatePulseHistories)s
        end if;
    end process;

    process (MyCLK, RST)
    begin
        if (RST='1') then
            LEDVal <= "00000001";
            Count <= (others=>'0');
        elsif (MyCLK'event and MyCLK='1') then
            Count <= Count + 1;
            if (Count="0000000000000000000000") then
                -- Update LEDs to show circuit is running...
                LEDVal <= LEDVal(6 downto 0) & LEDVal(7);
            end if;
        end if;
    end process;

    LEDs <= not LEDVal;

%(updateClockedPulses)s

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

    -- Loop back signals
    Sig <=  User_Signals(3 downto 0);
    process (CLK)
    begin
        if (CLK'event and CLK='1') then
            User_Signals(7 downto 4) <= Sig;
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

    -- Connections to the SystemC circuits
%(connectionsToSystemC)s

end arch;'''

makefile = '''SYSTEMC_SRC=                    \\
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
{tab}#-git commit -m "`date`" -a
{tab}mkdir -p "xst/projnav.tmp" || exit 1
{tab}xst -ise TASTE.ise -intstyle ise -ifn TASTE.xst -ofn TASTE.syr || exit 1
{tab}ngdbuild.exe -ise TASTE.ise -intstyle ise -dd _ngo -aul -nt timestamp -uc ZestSC1.ucf -p xc3s1000-ft256-5 TASTE.ngc TASTE.ngd|| exit 1
{tab}map -ise "TASTE.ise" -intstyle ise -p xc3s1000-ft256-5 -cm area -ir off -pr b -c 100 -o TASTE_map.ncd TASTE.ngd TASTE.pcf || exit 1
{tab}par -ise "TASTE.ise" -w -intstyle ise -ol std -t 1 TASTE_map.ncd TASTE.ncd TASTE.pcf || exit 1
{tab}trce -ise TASTE.ise -intstyle ise -e 3 -s 5 -xml TASTE.twx TASTE.ncd -o TASTE.twr TASTE.pcf || exit 1
{tab}bitgen -ise "TASTE.ise" -intstyle ise -f TASTE.ut TASTE.ncd || exit 1
{tab}cp "$@" ../TASTE.bit || exit 1

$(SYSTEMC_GENERATED):   $(SYSTEMC_SRC)
{tab}for i in $^ ; do if [ "`basename "$$i" | sed 's,^.*\.,,'`" = "cpp" ] ; then /c/Program\ Files/SystemCrafter/SystemCrafter\ SC/bin/craft.exe /vhdl $$i || exit 1; fi ; done

test:
{tab}cd .. ;  ./TASTE.exe

%%.clean:
{tab}-rm -f $*.stx $*.ucf.untf $*.mrp $*.nc1 $*.ngm $*.prm $*.lfp
{tab}-rm -f $*.placed_ncd_tracker $*.routed_ncd_tracker
{tab}-rm -f $*.pad_txt $*.twx *.log *.vhd~ $*.dhp $*.jhd $*.cel
{tab}-rm -f $*.ngr $*.ngc $*.ngd $*.syr $*.bld $*.pcf
{tab}-rm -f $*_map.map $*_map.mrp $*_map.ncd $*_map.ngm $*.ncd $*.pad
{tab}-rm -f $*.par $*.xpi $*_pad.csv $*_pad.txt $*.drc $*.bgn
{tab}-rm -f $*.xml $*_build.xml $*.rpt $*.gyd $*.mfd $*.pnx $*.ise
{tab}-rm -f $*.vm6 $*.jed $*.err $*.ER result.txt tmperr.err *.bak *.vhd~
{tab}-rm -f impactcmd.txt
{tab}-rm -f $*.twr $*_usage.xml
{tab}-rm -f $*.bit $*.svf $*.exo $*.mcs $*.ptwx $*.unroutes
{tab}-rm -f *_log *stx *summary.html *summary.xml
{tab}-rm -f $*_map.xrpt $*_ngdbuild.xrpt $*_par.xrpt $*_xst.xrpt
{tab}-rm -f *fdo *.xmsgs *.bld *.ngc *.ngd *.ncd
{tab}-rm -f *.bit *.mcs *.exo *.pcf *.twr
{tab}-rm -rf _ngo xst $*_xdb
{tab}-rm -f $(SYSTEMC_GENERATED)
{tab}-rm -f ../TASTE.bit

clean:  TASTE.clean
'''.format(tab='\t')

apbwrapper = '''------------------------------------------------------------------
-- This section is generated automatically by TASTE, DONT MODIFY it --
------------------------------------------------------------------
-- apbwrapper for user design declaration --

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_unsigned.all;

library grlib;
use grlib.amba.all;

use work.config.all;

entity apbwrapper2 is
{tab}generic(
{tab}{tab}--Configuration information--
{tab}{tab}pindex : integer;
{tab}{tab}paddr : integer;
{tab}{tab}pmask : integer
{tab}{tab});
{tab}port(
{tab}{tab}--Bus signals--
{tab}{tab}apbi : in  apb_slv_in_type;
{tab}{tab}apbo : out apb_slv_out_type;
{tab}{tab}
{tab}{tab}rst : in std_logic;
{tab}{tab}
{tab}{tab}clk : in std_logic
{tab}{tab}
{tab}{tab});
end apbwrapper2;

architecture archiapbwrapper2 of apbwrapper2 is

{tab}--Configuration declaration--
{tab}constant pconfig : apb_config_type := (
{tab}{tab}0 => ahb_device_reg ( 16#ff#, 1, 0, 1, 0),
{tab}{tab}1 => apb_iobar(paddr, pmask));
{tab}
{tab}--Type--{tab}
{tab}type registers_type is array(63 downto 0) of std_logic_vector(31 downto 0);
{tab}
{tab}--StartCalculation/CompletedCalculation signals--
%(startStopSignals)s
{tab}
{tab}--Size of the read and write registers area--
{tab}constant size_rw_area : integer := %(numberOfInputRegisters)s;
{tab}
{tab}--Custom Inputs and Outputs --
%(ioregisters)s
{tab}
%(circuits)s
{tab}
begin

{tab}--APB Slave Configuration--
{tab}apbo.pconfig <= pconfig;

{tab}-- -- CustomIP instanciation--
%(connectionsToSystemC)s
{tab}
{tab}--Read and write process--
{tab}read_write :
{tab}process(clk,rst)
{tab}{tab}variable sel : std_logic;
{tab}{tab}variable en : std_logic;
{tab}{tab}variable wr : std_logic;
{tab}{tab}variable add : std_logic_vector(7 downto 0);
{tab}{tab}variable ind : integer;
{tab}{tab}variable data_in : std_logic_vector(31 downto 0);
{tab}{tab}variable regs : registers_type;
{tab}begin
{tab}{tab}if rst='0' then -- Asynchronous Reset
{tab}{tab}
{tab}{tab}{tab}sel := '0';
{tab}{tab}{tab}en := '0';
{tab}{tab}{tab}wr := '0';
{tab}{tab}{tab}add := x"00";
{tab}{tab}{tab}ind := 0;
{tab}{tab}{tab}data_in := x"00000000";
{tab}{tab}{tab}regs := (others => (others => '0'));
%(reset)s
{tab}{tab}{tab}
{tab}{tab}elsif clk'event and clk='1' then
{tab}{tab}
{tab}{tab}{tab}-- AMBA bus signals extraction --
{tab}{tab}{tab}sel := apbi.psel(pindex); -- APB slave selected
{tab}{tab}{tab}en := apbi.penable; -- APB Slave action enabled
{tab}{tab}{tab}wr := apbi.pwrite; -- Write action
{tab}{tab}{tab}add := apbi.paddr(7 downto 0); -- 256 bytes address
{tab}{tab}{tab}data_in :=  apbi.pwdata; -- Receipt data to write
{tab}{tab}{tab}
{tab}{tab}{tab}ind := conv_integer(add(7 downto 2)); -- Registers index, read and write are possible only by step of 32 bits
{tab}{tab}{tab}
{tab}{tab}{tab}regs(0)(2) := %(pi)s_finish; -- Finish_compute is linked to bit 2 of Control/Command register
{tab}{tab}{tab}regs(0)(1) := regs(0)(0) and (not regs(0)(2)); -- Computation is running if start_compute is true and finish_compute is true
{tab}{tab}{tab}%(pi)s_start <= regs(0)(0); -- Drive start_compute
{tab}{tab}{tab}
{tab}{tab}{tab}-- Link Custom IP input variables with registers --
{tab}{tab}{tab}--custom_var_in_1 <= regs(1);
{tab}{tab}{tab}--custom_var_in_2 <= regs(2);
%(readinputdata)s
{tab}{tab}{tab}-- Link Custom IP output variables with registers --
{tab}{tab}{tab}--regs(3) := custom_var_out_1;
{tab}{tab}{tab}--regs(4) := custom_var_out_2;
%(writeoutputdata)s
{tab}{tab}{tab}apbo.prdata <= regs(ind); -- Read
{tab}{tab}{tab}
{tab}{tab}{tab}if (sel and (wr) and en) ='1' then -- Write
{tab}{tab}{tab}{tab}if ind = 0 then -- Control/Command register
{tab}{tab}{tab}{tab}{tab}regs(0)(0) := data_in(0);
{tab}{tab}{tab}{tab}elsif ind < size_rw_area+1 then -- Read and write registers area from 1 to size_rw_area
{tab}{tab}{tab}{tab}{tab}regs(ind) := data_in;
{tab}{tab}{tab}{tab}end if;
{tab}{tab}{tab}end if;
{tab}{tab}{tab}
{tab}{tab}{tab}
{tab}{tab}end if;
{tab}end process;

{tab}
end archiapbwrapper2;
'''.format(tab='\t')

apbwrapper_declaration = '''----------------------------------------------------------------------------------------------
-- THIS FILE IS GENERATED AUTOMATICALLY BY TASTE - DON'T MODIFY IT!!!
----------------------------------------------------------------------------------------------
-- Files       : Wrapper_Declaration.vhd
-- Version     : 0.2
-- Date        : 25/06/2010
-- Author      : Yann LECLERC - M3Systems
-- Co-author   : Thanassis Tsiodras - Semantix
--
----------------------------------------------------------------------------------------------
-- Description :
-- Declaration of wrapper component
--
-- In order to instanciate different custom IP, declaration of corresponding apbwrapper
-- component must be put to this file.
----------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
library grlib;
use grlib.amba.all;

package apbwrapper_declaration is

component apbwrapper0 is
        generic(
                --Configuration information--
                pindex : integer := 1;
                paddr : integer := 1;
                pmask : integer := 16#fff#
                );
        port(
                --Bus signals--
                apbi : in  apb_slv_in_type;
                apbo : out apb_slv_out_type;

                rst : in std_logic;

                clk : in std_logic

                );
end component;

component apbwrapper1 is
        generic(
                --Configuration information--
                pindex : integer := 1;
                paddr : integer := 1;
                pmask : integer := 16#fff#
                );
        port(
                --Bus signals--
                apbi : in  apb_slv_in_type;
                apbo : out apb_slv_out_type;

                rst : in std_logic;

                clk : in std_logic

                );
end component;

component apbwrapper2 is
        generic(
                --Configuration information--
                pindex : integer := 1;
                paddr : integer := 1;
                pmask : integer := 16#fff#
                );
        port(
                --Bus signals--
                apbi : in  apb_slv_in_type;
                apbo : out apb_slv_out_type;

                rst : in std_logic;

                clk : in std_logic

                );
end component;

end;
'''

architecture_top = '''-----------------------------------------------------------------------------
--
-- THIS FILE IS GENERATED AUTOMATICALLY BY TASTE - DON'T MODIFY IT!!!
--
-----------------------------------------------------------------------------
--  LEON3 Demonstration design
--  Copyright (C) 2004 Jiri Gaisler, Gaisler Research
------------------------------------------------------------------------------
--  This file is a part of the GRLIB VHDL IP LIBRARY
--  Copyright (C) 2003 - 2008, Gaisler Research
--  Copyright (C) 2008 - 2010, Aeroflex Gaisler
--
--  This program is free software; you can redistribute it and/or modify
--  it under the terms of the GNU General Public License as published by
--  the Free Software Foundation; either version 2 of the License, or
--  (at your option) any later version.
--
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--  GNU General Public License for more details.
--
--  You should have received a copy of the GNU General Public License
--  along with this program; if not, write to the Free Software
--  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
------------------------------------------------------------------------------
------------------------------------------------------------------------------
-- Files       : architecture_top.vhd
-- Version     : 0.1
-- Date        : 11/06/2010
-- Mofified by : Yann LECLERC - M3Systems
------------------------------------------------------------------------------
-- Description : This file is based on LEON3 Demonstration design.
-- It implements the different components of the architecture :
-- Gailser reset generator, clock generator, clock pads and PCI pads.
-- Gailser simple target PCI
-- Gailser AHB controller
-- Gailser APB bridge
-- APB wrappers
--
-- The index mapping on the AHB/APB bus is as follow :
-- Simple target PCI : AHB master 0
-- APB Bridge : AHB slave 0
-- APB wrappers : APB slave 0 to 1
--
-- The address mapping on the AHB/APB bus is as follow :
-- APB bridge : 0x80000000-0x80100000
-- APB wrappers: 256 bytes contiguous address space, mapped into APB bridge
-- address space from 0x80000000, thus:
-- APB wrapper 0 : 0x80000000-0x800000ff
-- APB wrapper 1 : 0x80000100-0x800001ff
--
-- The index of a wrapper on the APB bus, is defined throught the pindex
-- generic, its address throught the paddr generic (for example paddr=1 means
-- that wrapper address space is from 0x80000100 to 0x800001ff). The apbo port
-- of the wrapper is linked with apbo(index) signal.
--
-- In order to instanciate a new wrapper, the following constraints must be
-- met :
-- Maximum number of APB wrapper is 16
-- Index of the new wrapper must be different than those of the others
-- Address space of the new wrapper must not overlap those of the others
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

library grlib, techmap;
use grlib.amba.all;
use grlib.stdlib.all;
use techmap.gencomp.all;

library gaisler;
use gaisler.misc.all;
use gaisler.pci.all;

library m3s;
use m3s.apbwrapper_declaration.all;

use work.config.all;

entity TASTE_hardware_architecture is
  generic (
    fabtech   : integer := CFG_FABTECH;
    memtech   : integer := CFG_MEMTECH;
    padtech   : integer := CFG_PADTECH;
    clktech   : integer := CFG_CLKTECH
  );
  port (
    resetn{tab}: in  std_logic;
    clk{tab}{tab}: in  std_logic;
    pllref {tab}: in  std_logic;

    pci_rst     : inout std_logic;
    pci_clk {tab}: in std_logic;
    pci_gnt     : in std_logic;
    pci_idsel   : in std_logic;
    pci_lock    : inout std_logic;
    pci_ad {tab}: inout std_logic_vector(31 downto 0);
    pci_cbe {tab}: inout std_logic_vector(3 downto 0);
    pci_frame   : inout std_logic;
    pci_irdy {tab}: inout std_logic;
    pci_trdy {tab}: inout std_logic;
    pci_devsel  : inout std_logic;
    pci_stop {tab}: inout std_logic;
    pci_perr {tab}: inout std_logic;
    pci_par {tab}: inout std_logic;
    pci_req {tab}: inout std_logic;
    pci_serr    : inout std_logic;
    pci_host   {tab}: in std_logic;
    pci_66{tab}: in std_logic

{tab});
end;

architecture rtl of TASTE_hardware_architecture is

signal apbi  : apb_slv_in_type;
signal apbo  : apb_slv_out_vector := (others => apb_none);
signal ahbsi : ahb_slv_in_type;
signal ahbso : ahb_slv_out_vector := (others => ahbs_none);
signal ahbmi : ahb_mst_in_type;
signal ahbmo : ahb_mst_out_vector := (others => ahbm_none);

signal clkm, rstn, rstraw, pciclk, lclk, pci_lclk : std_logic;
signal cgi   : clkgen_in_type;
signal cgo   : clkgen_out_type;

signal pcii : pci_in_type;
signal pcio : pci_out_type;

constant BOARD_FREQ : integer := 50000;{tab}-- Board frequency in KHz


begin

----------------------------------------------------------------------
---  Reset and Clock generation  -------------------------------------
----------------------------------------------------------------------

{tab}cgi.pllctrl <= "00"; cgi.pllrst <= rstraw;

{tab}pllref_pad : clkpad
{tab}generic map (tech => padtech)
{tab}port map (pllref, cgi.pllref);

{tab}clk_pad : clkpad
{tab}generic map (tech => padtech)
{tab}port map (clk, lclk);

{tab}pci_clk_pad : clkpad
{tab}generic map (tech => padtech, level => pci33)
{tab}port map (pci_clk, pci_lclk);

{tab}clkgen0 : clkgen
    generic map (clktech, CFG_CLKMUL, CFG_CLKDIV, 0,
{tab}{tab}{tab}{tab}0, CFG_PCI, CFG_PCIDLL, CFG_PCISYSCLK, BOARD_FREQ)
    port map (lclk, pci_lclk, clkm, open, open, open, pciclk, cgi, cgo);

{tab}rst0 : rstgen
{tab}port map (resetn, clkm, cgo.clklock, rstn, rstraw);

----------------------------------------------------------------------
---  AHB CONTROLLER --------------------------------------------------
----------------------------------------------------------------------

{tab}ahb0 : ahbctrl
{tab}generic map (defmast => CFG_DEFMST, split => CFG_SPLIT,
{tab}{tab}{tab}{tab}rrobin => CFG_RROBIN, ioaddr => CFG_AHBIO,
{tab}{tab}{tab}{tab}ioen => 1,nahbm => 2, nahbs => 1)
{tab}port map (rstn, clkm, ahbmi, ahbmo, ahbsi, ahbso);

-----------------------------------------------------------------------
---  PCI Simple Target-------------------------------------------------
-----------------------------------------------------------------------

{tab}pci0 : pci_target
{tab}generic map (hindex => 0,device_id => CFG_PCIDID, vendor_id => CFG_PCIVID)
{tab}port map (rstn, clkm, pciclk, pcii, pcio, ahbmi, ahbmo(0));


{tab}pcipads0 : pcipads
{tab}generic map (padtech => padtech)
{tab}port map ( pci_rst, pci_gnt, pci_idsel, pci_lock, pci_ad, pci_cbe,
{tab}{tab}{tab}pci_frame, pci_irdy, pci_trdy, pci_devsel, pci_stop, pci_perr,
{tab}{tab}{tab}pci_par, pci_req, pci_serr, pci_host, pci_66, pcii, pcio );

----------------------------------------------------------------------
---  APB Bridge  -----------------------------------------------------
----------------------------------------------------------------------

{tab}apb0 : apbctrl
{tab}generic map (hindex => 0, haddr => CFG_APBADDR)
{tab}port map (rstn, clkm, ahbsi, ahbso(0), apbi, apbo );

-----------------------------------------------------------------------
---  Custom IP wrapper ------------------------------------------------
-----------------------------------------------------------------------

{tab}custom0 : apbwrapper0
{tab}generic map (pindex => 0, paddr => 0)
{tab}port map (apbi, apbo(0), rstn,clkm);

{tab}custom1 : apbwrapper1
{tab}generic map (pindex => 1, paddr => 1)
{tab}port map (apbi, apbo(1), rstn,clkm);

{tab}custom2 : apbwrapper2
{tab}generic map (pindex => 2, paddr => 2)
{tab}port map (apbi, apbo(2), rstn,clkm);

end;
'''.format(tab='\t')

customip2 = '''----------------------------------------------------------------------------------------------
--
-- THIS FILE IS GENERATED AUTOMATICALLY BY TASTE - DON'T MODIFY IT!!!
--
-----------------------------------------------------------------------------
-- Files       : customip2.vhd
-- Version     : 0.1
-- Date        : 07/06/2010
-- Co-author   : Thanassis Tsiodras - Semantix
----------------------------------------------------------------------------------------------
-- Description :
-- Automatically generated skeleton for your design.
-- You have to fill-in your processing logic, and set the finish flag when you're done
-- (see comments below)
----------------------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

use work.config.all;

%(entities)s

architecture archi%(pi)s of %(pi)s is

begin
{tab}process(clk_%(pi)s,rst_%(pi)s)
{tab}{tab}variable run : std_logic;
{tab}begin
{tab}{tab}if rst_%(pi)s='0' then -- Asynchronous reset

{tab}{tab}{tab}finish_%(pi)s <= '0';
                        -- write your resets here
{tab}{tab}{tab}run := '1';

{tab}{tab}elsif clk_%(pi)s'event and clk_%(pi)s='1' then

{tab}{tab}{tab}if start_%(pi)s = '0' then
{tab}{tab}{tab}{tab}finish_%(pi)s <= '0';
{tab}{tab}{tab}{tab}run := '1';
{tab}{tab}{tab}elsif run = '1' then

{tab}{tab}{tab}{tab}-- write your logic to compute outputs from inputs here
{tab}{tab}{tab}{tab}-- and when your results are ready, set...
{tab}{tab}{tab}{tab}--
{tab}{tab}{tab}{tab}-- run := '0';
{tab}{tab}{tab}{tab}-- finish_%(pi)s <= '1';
{tab}{tab}{tab}end if;
{tab}{tab}end if;
{tab}end process;
end archi%(pi)s;

'''.format(tab='\t')

architecture_config = '''-----------------------------------------------------------------------------
--
-- THIS FILE IS GENERATED AUTOMATICALLY BY TASTE - DON'T MODIFY IT!!!
--
-----------------------------------------------------------------------------
-- LEON3 Demonstration design test bench configuration
-- Copyright (C) 2009 Aeroflex Gaisler
------------------------------------------------------------------------------
------------------------------------------------------------------------------
-- Files       : architecture_config.vhd
-- Version     : 0.1
-- Date        : 11/06/2010
-- Mofified by : Yann LECLERC - M3Systems
------------------------------------------------------------------------------

library techmap;
use techmap.gencomp.all;

library ieee;
use ieee.std_logic_1164.all;

package config is
-- Technology and synthesis options
  constant CFG_FABTECH : integer := virtex4;
  constant CFG_MEMTECH : integer := virtex4;
  constant CFG_PADTECH : integer := virtex4;

-- Clock generator
  constant CFG_CLKTECH : integer := virtex4;

-- TASTE specific:
-- If your Synthesis reports that you have to lessen the clock,
-- (i.e. less than 100MHz) , you have to modify these two:
-- (default value: 2x50/1 = 100MHz
  constant CFG_CLKMUL : integer := (2);
  constant CFG_CLKDIV : integer := (1);

  constant CFG_PCIDLL : integer := 0;
  constant CFG_PCISYSCLK: integer := 0;
-- AMBA settings
  constant CFG_DEFMST : integer := (0);
  constant CFG_RROBIN : integer := 1;
  constant CFG_SPLIT : integer := 0;
  constant CFG_AHBIO : integer := 16#FFF#;
  constant CFG_APBADDR : integer := 16#800#;
-- PCI interface
  constant CFG_PCI : integer := 1;
  constant CFG_PCIVID : integer := 16#1AC8#;
  constant CFG_PCIDID : integer := 16#0054#;

-- TASTE specific:
-- types for byte arrays
%(octStr)s

end;
'''
