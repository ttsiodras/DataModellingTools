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
vhd = '''-- Company: GMV
-- Copyright European Space Agency, 2018

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library leon2ft;
use leon2ft.amba.all;

entity TASTE is
    port (
      clk_i    : in  std_logic;         -- System clock
      reset_n  : in  std_logic;         -- System RST
      -- APB interface
      apbi     : in  apb_slv_in_type;
      apbo     : out apb_slv_out_type;
      led_complete      : out std_logic;
      led_start         : out std_logic
    );
end TASTE;

architecture arch of TASTE is

    -- Circuits for the existing PIs
%(circuits)s
    -- Registers for I/O
%(ioregisters)s

    -- Signals for start/finish
%(startStopSignals)s

    -- Debug signals --
    signal led_start_reg		: std_logic;
    signal led_complete_reg		: std_logic;

begin

    led_complete	<= led_complete_reg;
    led_start		<= led_start_reg;

    -- Implement register write
    process (reset_n, clk_i)
    begin
        if (reset_n='0') then
            -- Signals for reset
%(reset)s
            led_start_reg               <= '0';
            led_complete_reg            <= '0';
        elsif (clk_i'event and clk_i='1') then
%(updateStartCompleteLedRegs)s
            -- Update start-stop pulses
%(updateStartStopPulses)s
            if (apbi.pwrite='1' and apbi.psel= '1' and apbi.penable = '1') then
                case (apbi.paddr(15 downto 0)) is
                      -- Read data
%(readinputdata)s
                 end case;
            end if;
%(setStartSignalsLow)s
        end if;
    end process;

    -- Implement register read
    process (apbi.paddr, apbi.pwrite, apbi.psel, %(outputs)s %(completions)s)
    begin
        apbo.prdata <= (others => '0');
        if (apbi.pwrite='0' and apbi.psel= '1') then
            case (apbi.paddr(15 downto 0)) is
                -- Write data
%(writeoutputdata)s
                when others => apbo.prdata(7 downto 0) <= (others => '0');
            end case;
        end if;
    end process;

    -- Connections to the VHDL circuits
%(connectionsToSystemC)s

    process(reset_n, clk_i)
    begin
        if (reset_n='0') then
%(updateCalculationsCompleteReset)s
        elsif (clk_i'event and clk_i='1') then
%(updateCalculationsComplete)s
        end if;
    end process;

end arch;'''

makefile = r'''
SRCS=TASTE.vhd %(pi)s

all:   ${SRCS}
%(tab)snanoxpython script.py
%(tab)spython swap.py bitfile.nxb bitfile-swapped.nxb

clean:
%(tab)srm -rf logs *.nxm *.pyc *.nxb
'''

per_circuit_vhd = """-- Company: GMV
-- Copyright European Space Agency, 2018

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

%(declaration)s

architecture arch of bambu_%(pi)s is

    -- Declare signals
    signal CLK : std_logic;
    signal RST : std_logic;

    signal state : unsigned(1 downto 0);
begin

    CLK <= clock_%(pi)s;
    RST <= reset_%(pi)s;

    -- Possible clock divider
    process(CLK, RST)
    begin
        if (RST='0') then
            finish_%(pi)s <= '0'; -- or 1?
            state                    <= "00";
            -- outp                     <= (others => '0');
        elsif (CLK'event and CLK='1') then
            case state is
                when "00" =>
                    if start_%(pi)s = '1' then
                        state <= "01";
                        finish_%(pi)s <= '0';
                    end if;
                when "01" =>

                    -----------------------------
                    -- Do your processing here --
                    -----------------------------

                    state <= "10";
                when "10" =>
                    finish_%(pi)s <= '1';
                    state <= "00";
                when others =>
                  state <= "00";
            end case;
        end if;
    end process;

end arch;
"""

script = """import os
import sys

from os import path
from nanoxmap import *

dir = os.path.dirname(os.path.realpath(__file__))

sys.path.append(dir)

#setVerbosity(0)

project = createProject(dir)

project.setVariantName('NG-MEDIUM')

project.setTopCellName('top_lib', 'rdhc_bb')

project.addFiles('leon2ft', [
'../src/leon2ft_2015.3_nomeiko/leon/amba.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/target.vhd',
'device.vhd',
'TASTE.vhd',%(pi)s
'../src/leon2ft_2015.3_nomeiko/leon/config.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/ftlib.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/ftcell.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/sparcv8.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/mmuconfig.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/iface.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/macro.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/ambacomp.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/bprom.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/multlib.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_generic.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_atc18.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_atc25.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_atc35.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_fs90.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_umc18.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_tsmc25.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_virtex.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_virtex2.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_proasic.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_axcel.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/tech_map.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/dsu.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/dsu_mem.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/dcom_uart.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/dcom.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/rstgen.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/irqctrl.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/ioport.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/timers.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/uart.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/ahbmst.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/apbmst.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/ahbram.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/ahbarb.vhd',
'../src/leon2ft_2015.3_nomeiko/leon/mccomp.vhd'])

project.addFiles('spwrmap', [
'../src/rmap_core_v1_00_enduser_release/src/vhdl/pkg/support_pkg.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/rmap_pkg.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/dma/dma_pkg.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/pkg/tech_pkg.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/spw/spwrlink_pkg.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/initfsm/initfsm_counter.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/initfsm/initfsm_sync.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/initfsm/init_fsm.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/other/clk10gen.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/other/clkmux.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/receive/rxclock.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/receive/rxcredit.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/receive/rxdataformat.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/receive/rxdecode.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/receive/rxdiscerr.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/receive/rxnchar_resync_valid.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/receive/rxnchar_resync_ffstore_inferfpgaram.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/receive/rxnchar_resync_ff.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/receive/rxtcode_resync.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/transmit/txddrreg.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/transmit/txddrreg_noenable.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/transmit/txencode.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/transmit/txtcode_send.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/txclk/txclk_divider.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/txclk/txclk_en_gen.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/txclk/txclkgen.vhd',
'../src/rmap_core_v1_00_enduser_release/extern/uodcodec_cvsrel_2_03/src/vhdl/top/spwrlink.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/mem/fifo_out_valid.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/sync_fifo/sync_fifo_logic.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/sync_fifo/sync_dpfifo.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/sync_fifo/sync_memblock_fpga_memory.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/async_fifo/async_dpfifo.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/async_fifo/async_fifo_logic.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/async_fifo/async_fifo_readptr.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/async_fifo/async_fifo_writeptr.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/async_fifo/async_memblock_fpga_memory.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/spw/spwrlinkwrap.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/spw/protocol_mux.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/spw/protocol_demux.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/spw/timecode_handler.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/spw/timecode_handler.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/dma/bus_arbiter.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/dma/dma_controller.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/dma/dma_burst_fifo_in.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/dma/dma_burst_fifo_out.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/dma/bus_master.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/unpack_rmap_word.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/pack_rmap_word.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/target_command_decode.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/target_reply_encode.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/target_controller.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/target_verify_control.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/rmap_target.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/unpack_rmap_word.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/pack_rmap_word.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/ini_command_encode.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/ini_reply_decode.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/ini_trans_controller.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/ini_delete.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/rmap/rmap_initiator.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/top/rmap_kernel.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/top/verify_buffer.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl//mem/ax_table_32x4.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl//mem/ax_table_32x5.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl//mem/ax_table_32x6.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl//mem/ax_table_32x7.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl//mem/ax_table_32x8.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl//mem/pa3_table_32x4.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl//mem/pa3_table_32x5.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl//mem/pa3_table_32x6.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl//mem/pa3_table_32x7.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl//mem/pa3_table_32x8.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/mem/transaction_table.vhd',
'../src/rmap_core_v1_00_enduser_release/src/vhdl/top/rmap_codec_ip.vhd',
'rmap_amba.vhd'])

project.addFiles('bravecomp', ['clkgen_bm.vhd'])
project.addFiles('top_lib', ['rdhc_bb.vhd'])

project.setOptions({'UseNxLibrary': 'Yes',
                    'MergeRegisterToPad': 'Always',
                    'ManageUnconnectedOutputs': 'Ground',
                    'ManageUnconnectedSignals': 'Ground',
                    'ManageAsynchronousReadPort': 'Yes',
                    'DefaultRAMMapping': 'RAM'})
project.addMappingDirective('getModels(.*regfile_3p.*)', 'RAM', 'RF')
#=======================================================================================================
# Assigning timing constraints
#=======================================================================================================
# Defining the clock periods
project.createClock('getClockNet(clk25)', 'clk25', 40000, 0, 20000) # Period = 40000 ps, # first rising edge at 20000 ps -- 25 MHz
project.createClock('getClockNet(txclk)', 'txclk', 20000, 0, 10000) # Period = 20000 ps, # first rising edge at 10000 ps -- 50 MHz
project.createClock('getClockNet(spw.swloop[0].spw|rmap_codec_ip_1|spwrlinkwrap_1|spwrlink_1|RX_CLK)', 'rxclk', 20000, 0, 10000) # Period = 20000 ps, # first rising edge at 10000 ps -- 50 MHz

project.setClockGroup('getClock(clk25)', 'getClock(txclk)', 'asynchronous')
project.setClockGroup('getClock(txclk)', 'getClock(clk25)', 'asynchronous')
project.setClockGroup('getClock(rxclk)', 'getClock(txclk)', 'asynchronous')
project.setClockGroup('getClock(txclk)', 'getClock(rxclk)', 'asynchronous')
project.setClockGroup('getClock(clk25)', 'getClock(rxclk)', 'asynchronous')
project.setClockGroup('getClock(rxclk)', 'getClock(clk25)', 'asynchronous')
#=======================================================================================================

if path.exists(dir + '/pads.py'):
    from pads import pads
    project.addPads(pads)

project.save('native.nxm')

if not project.synthesize():
    sys.exit(1)

project.save('synthesized.nxm')

if not project.place():
    sys.exit(1)

project.save('placed.nxm')

if not path.exists(dir + '/pads.py'):
    project.savePorts('pads.py')

if not project.route():
    sys.exit(1)

project.save('routed.nxm')

project.save('routed.vhd')

#reports
project.reportInstances()

#STA
analyzer = project.createAnalyzer()

analyzer.launch()

#bitstream
project.generateBitstream('bitfile.nxb')
print 'Errors: ', getErrorCount()
print 'Warnings: ', getWarningCount()

"""
