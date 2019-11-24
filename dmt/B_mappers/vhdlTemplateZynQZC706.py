# Company: GMV
# Copyright European Space Agency, 2019-2020

vhd = '''-- Company: GMV
-- Copyright European Space Agency, 2019-2020

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- import needed IPs

entity TASTE is
    port (
      clk_i    : in  std_logic;         -- System clock
      reset_n  : in  std_logic;         -- System RST
      -- AXI interface
      axii     : in  axi_slv_in_type;
      axio     : out axi_slv_out_type;
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
            if (axii.pwrite='1' and axii.psel= '1' and axii.penable = '1') then
                case (axii.paddr(15 downto 0)) is
                      -- Read data
%(readinputdata)s
                 end case;
            end if;
%(setStartSignalsLow)s
        end if;
    end process;

    -- Implement register read
    process (axii.paddr, axii.pwrite, axii.psel, %(outputs)s %(completions)s)
    begin
        axio.prdata <= (others => '0');
        if (axii.pwrite='0' and axii.psel= '1') then
            case (axii.paddr(15 downto 0)) is
                -- Write data
%(writeoutputdata)s
                when others => axio.prdata(7 downto 0) <= (others => '0');
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

#TODO
makefile = r'''-- Company: GMV
-- Copyright European Space Agency, 2019-2020
'''

per_circuit_vhd = """-- Company: GMV
-- Copyright European Space Agency, 2019-2020

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

# TODO
script = """-- Company: GMV
-- Copyright European Space Agency, 2019-2020
"""
