# Company: GMV
# Copyright European Space Agency, 2019-2020

vhd = '''--------------------------------------------------------------------------------
-- Company: GMV Aerospace & Defence S.A.U.
-- Copyright European Space Agency, 2019-2020
--------------------------------------------------------------------------------
--   __ _ _ __ _____   __
--  / _` | '_ ` _ \ \ / /   Company:	GMV Aerospace & Defence S.A.U.
-- | (_| | | | | | \ V /    Author: 	Ruben Domingo Torrijos (rdto@gmv.com)
--  \__, |_| |_| |_|\_/     Module: 	TASTE
--   __/ |               
--  |___/              
-- 
-- Create Date: 18/09/2019
-- Design Name: TASTE
-- Module Name: TASTE
-- Project Name: Cora-mbad-4zynq
-- Target Devices: XC7Z045
-- Tool versions: Vivado 2019
-- Description: Interface between Zynq proccesor and Bambu IP through AXI_LITE
--
-- Dependencies:
--
-- Revision: 
-- Revision 0.01 - File Created
-- Additional Comments: 
--
----------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity TASTE is
	generic (
		ADD_BUS_SIZE			: integer 		:= 16;
		ADD_ALIGNEMENT			: integer		:= 4;
		ADD_W_START				: integer		:= 768;		-- X"0300"
		ADD_R_START				: integer		:= 908		-- X"038C"
		);
    port (
		-- Clock and Reset
		S_AXI_ACLK				: in  std_logic;
		S_AXI_ARESETN			: in  std_logic;
		-- Write Address Channel
		S_AXI_AWADDR			: in  std_logic_vector(31 downto 0);
		S_AXI_AWVALID			: in  std_logic;
		S_AXI_AWREADY			: out std_logic;
		-- Write Data Channel
		S_AXI_WDATA				: in  std_logic_vector(31 downto 0);
		S_AXI_WSTRB				: in  std_logic_vector(3 downto 0);
		S_AXI_WVALID			: in  std_logic;
		S_AXI_WREADY			: out std_logic;
		-- Read Address Channel
		S_AXI_ARADDR			: in  std_logic_vector(31 downto 0);
		S_AXI_ARVALID			: in  std_logic;
		S_AXI_ARREADY			: out std_logic;
		-- Read Data Channel
		S_AXI_RDATA				: out std_logic_vector(31 downto 0);
		S_AXI_RRESP				: out std_logic_vector(1 downto 0);
		S_AXI_RVALID			: out std_logic;
		S_AXI_RREADY			: in  std_logic;
		-- Write Response Channel
		S_AXI_BRESP				: out std_logic_vector(1 downto 0);
		S_AXI_BVALID			: out std_logic;
		S_AXI_BREADY			: in  std_logic;
		-- Debug signals
		start_led				: out std_logic;
		done_led				: out std_logic
    );
end TASTE;

architecture rtl of TASTE is

	---------------------------------------------------
	--			  COMPONENT DECLARATION			 	 --
	---------------------------------------------------	
    -- Circuits for the existing PIs
%(circuits)s
	
	---------------------------------------------------
	--				TYPES DECLARATION			 	 --
	---------------------------------------------------		
	-- AXI FSM states
	type AXI_states is(idle, reading, r_complete, writing, wait_resp);
	
	-- AXI combinational outputs record
	type AXI_comb_out is record
	
		awready						: std_logic;
		wready						: std_logic;
		arready						: std_logic;
		rdata						: std_logic_vector(31 downto 0);
		rresp						: std_logic_vector(1 downto 0);
		rvalid						: std_logic;
		bvalid						: std_logic;
	
	end record;
	
	-- AXI internal signals record
	type AXI_inter is record
	
		currentState								: AXI_states;
		r_local_address								: integer;
		bresp										: std_logic_vector(1 downto 0);
		%(pi)s_StartCalculationsInternal		: std_logic;
		%(pi)s_StartCalculationsInternalOld	: std_logic;
		start_led									: std_logic;
		done_led									: std_logic;
	
	end record;	

	---------------------------------------------------
	--			  CONSTANTS DECLARATION			 	 --
	---------------------------------------------------		
	constant OKAY					: std_logic_vector(1 downto 0) 		:= "00";
	constant EXOKAY					: std_logic_vector(1 downto 0) 		:= "01";
	constant SLVERR					: std_logic_vector(1 downto 0) 		:= "10";
	constant DECERR					: std_logic_vector(1 downto 0) 		:= "11";	

	constant INIT_AXI_comb_out		: AXI_comb_out 						:= (awready				=> '0',	
																			wready				=> '0',
																			arready				=> '0',
                                                                            rdata				=> (others => '0'),
                                                                            rresp				=> OKAY,
                                                                            rvalid				=> '0',
                                                                            bvalid				=> '0');

	constant INIT_AXI_inter			: AXI_inter 						:= (currentState								=> idle,
																			r_local_address								=> 0,
																			bresp										=> OKAY,
																			%(pi)s_StartCalculationsInternal		=> '0',
																			%(pi)s_StartCalculationsInternalOld	=> '0',
																			start_led									=> '1',
																			done_led									=> '0');																		
	---------------------------------------------------
	--				SIGNAL DECLARATION			 	 --
	---------------------------------------------------	
    -- Registers for I/O
%(ioregisters)s

    -- Signals for start/finish
%(startStopSignals)s
	
	-- AXI contrl Signals
	signal r											: AXI_inter;
	signal rin											: AXI_inter;
	signal r_comb_out									: AXI_comb_out;
	signal rin_comb_out									: AXI_comb_out;	

begin

	---------------------------------------------------
	--				COMPONENT INSTANTITATION		 --
	---------------------------------------------------
    -- Connections to the VHDL circuits
%(connectionsToSystemC)s

	---------------------------------------------------
	--				PROCESS INSTANTIATION		     --
	---------------------------------------------------		
	-- Sequential process --
	sequential:	process(S_AXI_ACLK)
	begin 		
		if rising_edge(S_AXI_ACLK) then
			r				<= rin;
			r_comb_out		<= rin_comb_out;
		end if;
	end process;

	-- Combinational process --	
	combinational: process(	-- internal signals --
							r, r_comb_out,
							-- AXI inptuts --
							S_AXI_ARESETN, S_AXI_AWADDR, S_AXI_AWVALID, S_AXI_WDATA, S_AXI_WSTRB, S_AXI_WVALID, S_AXI_ARADDR, S_AXI_ARVALID, S_AXI_RREADY, S_AXI_BREADY,
							-- Bambu signals --
							%(outputs)s %(starts)s, %(completions)s
							)
							
		variable v									: AXI_inter;
		variable v_comb_out							: AXI_comb_out;
		variable comb_S_AXI_AWVALID_S_AXI_ARVALID	: std_logic_vector(1 downto 0);
		variable w_local_address					: integer;
		
	begin
	
		---------------------------------------------------
		--			DEFAULT VARIABLES ASIGNATION		 --
		---------------------------------------------------
		v 											:= r;		
		-----------------------------------------------------------------
		--	 	DEFAULT COMBINATIONAL OUTPUT VARIABLES ASIGNATION      --
		-----------------------------------------------------------------
		v_comb_out									:= INIT_AXI_comb_out;
		if %(pi)s_StartCalculationsPulse = '1' then
			v.start_led								:= not r.start_led;
			v.done_led								:= '0';
		end if;
		if %(pi)s_CalculationsComplete = '1' then
			v.done_led								:= '1';
		end if;
		-----------------------------------------------------------------
		--	 			DEFAULT INTERNAL VARIABLE ASIGNATION      	   --
		-----------------------------------------------------------------		
		w_local_address								:= to_integer(unsigned(S_AXI_AWADDR(ADD_BUS_SIZE-1 downto 0)));		
		comb_S_AXI_AWVALID_S_AXI_ARVALID			:= S_AXI_AWVALID&S_AXI_ARVALID;	
		
		-- Update start-stop pulses
		v.%(pi)s_StartCalculationsInternalOld 	:= r.%(pi)s_StartCalculationsInternal;
	
		case r.currentState is
			when idle =>
				v.bresp					:= OKAY;
				case comb_S_AXI_AWVALID_S_AXI_ARVALID is
					when "01" 	=> 
						v.currentState 	:= reading;
					when "11" 	=> 
						v.currentState 	:= reading;
					when "10" 	=> 
						v.currentState 	:= writing;
					when others	=> 
						v.currentState 	:= idle;
				end case;			
			
			when writing =>
				v_comb_out.awready		:= S_AXI_AWVALID;
				v_comb_out.wready		:= S_AXI_WVALID;
				v.bresp					:= r.bresp;				
				if S_AXI_WVALID = '1' then
					v.currentState	:= wait_resp;
					case w_local_address is
%(readinputdata)s
					end case;
				end if;
				
			when wait_resp =>
				v_comb_out.awready		:= S_AXI_AWVALID;
				v_comb_out.wready		:= S_AXI_WVALID;
				v.bresp					:= r.bresp;
				v_comb_out.bvalid		:= S_AXI_BREADY;
				if S_AXI_AWVALID = '0' then
					v.currentState := idle;
				else
					if S_AXI_WVALID = '1' then
						case w_local_address is
%(readinputdata)s
						end case;
					else
						v.currentState := writing;
					end if;
				end if;
			
			when reading =>
				v_comb_out.arready		:= S_AXI_ARVALID;
				v.bresp					:= OKAY;
				v.r_local_address		:= to_integer(unsigned(S_AXI_ARADDR(ADD_BUS_SIZE-1 downto 0)));
				v.currentState 			:= r_complete;
			when r_complete => 
				v_comb_out.arready		:= S_AXI_ARVALID;
				v_comb_out.rvalid		:= '1';
				v.bresp					:= OKAY;
				if S_AXI_RREADY = '1' then
					if S_AXI_ARVALID = '0' then
						v.currentState 		:= idle;
					else
						v.r_local_address	:= to_integer(unsigned(S_AXI_ARADDR(ADD_BUS_SIZE-1 downto 0)));
					end if;
				end if;
				case r.r_local_address is
%(writeoutputdata)s
					when others =>
						v_comb_out.rdata(31 downto 0) 	:= (others => '0');								
				end case;
		end case;

		---------------------------------------------------
		--				  RESET ASIGNATION		 	     --
		---------------------------------------------------		
		if S_AXI_ARESETN = '0' then
			v		    			:= INIT_AXI_inter;
			v_comb_out				:= INIT_AXI_comb_out;
		end if;

		---------------------------------------------------
		--				SIGNAL ASIGNATION			     --
		---------------------------------------------------		
		rin 	          	<= v;
		rin_comb_out		<= v_comb_out;
		
	end process;	

	---------------------------------------------------
	--		   INTERNAL ARCHITECTURE SIGNALS	 	 --
	---------------------------------------------------		
	%(pi)s_StartCalculationsPulse 			<= r.%(pi)s_StartCalculationsInternal xor r.%(pi)s_StartCalculationsInternalOld;
	
	---------------------------------------------------
	--					 OUTPUTS	 	 			 --
	---------------------------------------------------	
	S_AXI_AWREADY			<= rin_comb_out.awready;
	S_AXI_WREADY			<= rin_comb_out.wready;
	S_AXI_ARREADY			<= rin_comb_out.arready;
	S_AXI_RDATA				<= rin_comb_out.rdata;
	S_AXI_RRESP				<= rin_comb_out.rresp;
	S_AXI_RVALID			<= rin_comb_out.rvalid;
	S_AXI_BRESP				<= rin.bresp;
	S_AXI_BVALID			<= rin_comb_out.bvalid;
	start_led				<= r.start_led;
	done_led				<= r.done_led;	
	
end rtl;'''

makefile = r'''
SRCS=../ip/src/TASTE2.vhd %(pi)s

all:   ${SRCS}
%(tab)s@echo "Now we would call vivado... to be done (should be: vivado -mode batch -source TASTE2.tcl)"

clean:
%(tab)srm -rf *.bit
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

component_xml = """<?xml version="1.0" encoding="UTF-8"?>
<spirit:component xmlns:xilinx="http://www.xilinx.com" xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <spirit:vendor>user.org</spirit:vendor>
  <spirit:library>user</spirit:library>
  <spirit:name>TASTE</spirit:name>
  <spirit:version>1.0</spirit:version>
  <spirit:busInterfaces>
    <spirit:busInterface>
      <spirit:name>S_AXI</spirit:name>
      <spirit:busType spirit:vendor="xilinx.com" spirit:library="interface" spirit:name="aximm" spirit:version="1.0"/>
      <spirit:abstractionType spirit:vendor="xilinx.com" spirit:library="interface" spirit:name="aximm_rtl" spirit:version="1.0"/>
      <spirit:slave>
        <spirit:memoryMapRef spirit:memoryMapRef="S_AXI"/>
      </spirit:slave>
      <spirit:portMaps>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>AWADDR</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_AWADDR</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>AWVALID</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_AWVALID</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>AWREADY</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_AWREADY</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>WDATA</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_WDATA</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>WSTRB</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_WSTRB</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>WVALID</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_WVALID</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>WREADY</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_WREADY</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>BRESP</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_BRESP</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>BVALID</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_BVALID</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>BREADY</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_BREADY</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>ARADDR</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_ARADDR</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>ARVALID</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_ARVALID</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>ARREADY</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_ARREADY</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>RDATA</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_RDATA</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>RRESP</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_RRESP</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>RVALID</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_RVALID</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>RREADY</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_RREADY</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
      </spirit:portMaps>
    </spirit:busInterface>
    <spirit:busInterface>
      <spirit:name>S_AXI_ARESETN</spirit:name>
      <spirit:busType spirit:vendor="xilinx.com" spirit:library="signal" spirit:name="reset" spirit:version="1.0"/>
      <spirit:abstractionType spirit:vendor="xilinx.com" spirit:library="signal" spirit:name="reset_rtl" spirit:version="1.0"/>
      <spirit:slave/>
      <spirit:portMaps>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>RST</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_ARESETN</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
      </spirit:portMaps>
      <spirit:parameters>
        <spirit:parameter>
          <spirit:name>POLARITY</spirit:name>
          <spirit:value spirit:id="BUSIFPARAM_VALUE.S_AXI_ARESETN.POLARITY" spirit:choiceRef="choice_list_9d8b0d81">ACTIVE_LOW</spirit:value>
        </spirit:parameter>
      </spirit:parameters>
    </spirit:busInterface>
    <spirit:busInterface>
      <spirit:name>S_AXI_ACLK</spirit:name>
      <spirit:busType spirit:vendor="xilinx.com" spirit:library="signal" spirit:name="clock" spirit:version="1.0"/>
      <spirit:abstractionType spirit:vendor="xilinx.com" spirit:library="signal" spirit:name="clock_rtl" spirit:version="1.0"/>
      <spirit:slave/>
      <spirit:portMaps>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>CLK</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXI_ACLK</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
      </spirit:portMaps>
      <spirit:parameters>
        <spirit:parameter>
          <spirit:name>ASSOCIATED_BUSIF</spirit:name>
          <spirit:value spirit:id="BUSIFPARAM_VALUE.S_AXI_ACLK.ASSOCIATED_BUSIF">S_AXI</spirit:value>
        </spirit:parameter>
        <spirit:parameter>
          <spirit:name>ASSOCIATED_RESET</spirit:name>
          <spirit:value spirit:id="BUSIFPARAM_VALUE.S_AXI_ACLK.ASSOCIATED_RESET">S_AXI_ARESETN</spirit:value>
        </spirit:parameter>
      </spirit:parameters>
    </spirit:busInterface>
  </spirit:busInterfaces>
  <spirit:memoryMaps>
    <spirit:memoryMap>
      <spirit:name>S_AXI</spirit:name>
      <spirit:addressBlock>
        <spirit:name>reg0</spirit:name>
        <spirit:baseAddress spirit:format="bitString" spirit:resolve="user" spirit:bitStringLength="32">0</spirit:baseAddress>
        <spirit:range spirit:format="long" spirit:resolve="user" spirit:minimum="4096" spirit:rangeType="long">65536</spirit:range>
        <spirit:width spirit:format="long" spirit:resolve="user">32</spirit:width>
        <spirit:usage>register</spirit:usage>
      </spirit:addressBlock>
    </spirit:memoryMap>
  </spirit:memoryMaps>
  <spirit:model>
    <spirit:views>
      <spirit:view>
        <spirit:name>xilinx_anylanguagesynthesis</spirit:name>
        <spirit:displayName>Synthesis</spirit:displayName>
        <spirit:envIdentifier>:vivado.xilinx.com:synthesis</spirit:envIdentifier>
        <spirit:language>VHDL</spirit:language>
        <spirit:modelName>TASTE</spirit:modelName>
        <spirit:fileSetRef>
          <spirit:localName>xilinx_anylanguagesynthesis_view_fileset</spirit:localName>
        </spirit:fileSetRef>
        <spirit:parameters>
          <spirit:parameter>
            <spirit:name>viewChecksum</spirit:name>
            <spirit:value>bbbda21a</spirit:value>
          </spirit:parameter>
        </spirit:parameters>
      </spirit:view>
      <spirit:view>
        <spirit:name>xilinx_anylanguagebehavioralsimulation</spirit:name>
        <spirit:displayName>Simulation</spirit:displayName>
        <spirit:envIdentifier>:vivado.xilinx.com:simulation</spirit:envIdentifier>
        <spirit:language>VHDL</spirit:language>
        <spirit:modelName>TASTE</spirit:modelName>
        <spirit:fileSetRef>
          <spirit:localName>xilinx_anylanguagebehavioralsimulation_view_fileset</spirit:localName>
        </spirit:fileSetRef>
        <spirit:parameters>
          <spirit:parameter>
            <spirit:name>viewChecksum</spirit:name>
            <spirit:value>bbbda21a</spirit:value>
          </spirit:parameter>
        </spirit:parameters>
      </spirit:view>
      <spirit:view>
        <spirit:name>xilinx_xpgui</spirit:name>
        <spirit:displayName>UI Layout</spirit:displayName>
        <spirit:envIdentifier>:vivado.xilinx.com:xgui.ui</spirit:envIdentifier>
        <spirit:fileSetRef>
          <spirit:localName>xilinx_xpgui_view_fileset</spirit:localName>
        </spirit:fileSetRef>
        <spirit:parameters>
          <spirit:parameter>
            <spirit:name>viewChecksum</spirit:name>
            <spirit:value>1c7a8e6b</spirit:value>
          </spirit:parameter>
        </spirit:parameters>
      </spirit:view>
    </spirit:views>
    <spirit:ports>
      <spirit:port>
        <spirit:name>S_AXI_ACLK</spirit:name>
        <spirit:wire>
          <spirit:direction>in</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_ARESETN</spirit:name>
        <spirit:wire>
          <spirit:direction>in</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_AWADDR</spirit:name>
        <spirit:wire>
          <spirit:direction>in</spirit:direction>
          <spirit:vector>
            <spirit:left spirit:format="long">31</spirit:left>
            <spirit:right spirit:format="long">0</spirit:right>
          </spirit:vector>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic_vector</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
          <spirit:driver>
            <spirit:defaultValue spirit:format="long">0</spirit:defaultValue>
          </spirit:driver>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_AWVALID</spirit:name>
        <spirit:wire>
          <spirit:direction>in</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
          <spirit:driver>
            <spirit:defaultValue spirit:format="long">0</spirit:defaultValue>
          </spirit:driver>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_AWREADY</spirit:name>
        <spirit:wire>
          <spirit:direction>out</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_WDATA</spirit:name>
        <spirit:wire>
          <spirit:direction>in</spirit:direction>
          <spirit:vector>
            <spirit:left spirit:format="long">31</spirit:left>
            <spirit:right spirit:format="long">0</spirit:right>
          </spirit:vector>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic_vector</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
          <spirit:driver>
            <spirit:defaultValue spirit:format="long">0</spirit:defaultValue>
          </spirit:driver>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_WSTRB</spirit:name>
        <spirit:wire>
          <spirit:direction>in</spirit:direction>
          <spirit:vector>
            <spirit:left spirit:format="long">3</spirit:left>
            <spirit:right spirit:format="long">0</spirit:right>
          </spirit:vector>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic_vector</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
          <spirit:driver>
            <spirit:defaultValue spirit:format="long">1</spirit:defaultValue>
          </spirit:driver>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_WVALID</spirit:name>
        <spirit:wire>
          <spirit:direction>in</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
          <spirit:driver>
            <spirit:defaultValue spirit:format="long">0</spirit:defaultValue>
          </spirit:driver>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_WREADY</spirit:name>
        <spirit:wire>
          <spirit:direction>out</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_ARADDR</spirit:name>
        <spirit:wire>
          <spirit:direction>in</spirit:direction>
          <spirit:vector>
            <spirit:left spirit:format="long">31</spirit:left>
            <spirit:right spirit:format="long">0</spirit:right>
          </spirit:vector>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic_vector</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
          <spirit:driver>
            <spirit:defaultValue spirit:format="long">0</spirit:defaultValue>
          </spirit:driver>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_ARVALID</spirit:name>
        <spirit:wire>
          <spirit:direction>in</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
          <spirit:driver>
            <spirit:defaultValue spirit:format="long">0</spirit:defaultValue>
          </spirit:driver>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_ARREADY</spirit:name>
        <spirit:wire>
          <spirit:direction>out</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_RDATA</spirit:name>
        <spirit:wire>
          <spirit:direction>out</spirit:direction>
          <spirit:vector>
            <spirit:left spirit:format="long">31</spirit:left>
            <spirit:right spirit:format="long">0</spirit:right>
          </spirit:vector>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic_vector</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_RRESP</spirit:name>
        <spirit:wire>
          <spirit:direction>out</spirit:direction>
          <spirit:vector>
            <spirit:left spirit:format="long">1</spirit:left>
            <spirit:right spirit:format="long">0</spirit:right>
          </spirit:vector>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic_vector</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_RVALID</spirit:name>
        <spirit:wire>
          <spirit:direction>out</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_RREADY</spirit:name>
        <spirit:wire>
          <spirit:direction>in</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
          <spirit:driver>
            <spirit:defaultValue spirit:format="long">0</spirit:defaultValue>
          </spirit:driver>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_BRESP</spirit:name>
        <spirit:wire>
          <spirit:direction>out</spirit:direction>
          <spirit:vector>
            <spirit:left spirit:format="long">1</spirit:left>
            <spirit:right spirit:format="long">0</spirit:right>
          </spirit:vector>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic_vector</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_BVALID</spirit:name>
        <spirit:wire>
          <spirit:direction>out</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>S_AXI_BREADY</spirit:name>
        <spirit:wire>
          <spirit:direction>in</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
          <spirit:driver>
            <spirit:defaultValue spirit:format="long">0</spirit:defaultValue>
          </spirit:driver>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>start_led</spirit:name>
        <spirit:wire>
          <spirit:direction>out</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
      <spirit:port>
        <spirit:name>done_led</spirit:name>
        <spirit:wire>
          <spirit:direction>out</spirit:direction>
          <spirit:wireTypeDefs>
            <spirit:wireTypeDef>
              <spirit:typeName>std_logic</spirit:typeName>
              <spirit:viewNameRef>xilinx_anylanguagesynthesis</spirit:viewNameRef>
              <spirit:viewNameRef>xilinx_anylanguagebehavioralsimulation</spirit:viewNameRef>
            </spirit:wireTypeDef>
          </spirit:wireTypeDefs>
        </spirit:wire>
      </spirit:port>
    </spirit:ports>
    <spirit:modelParameters>
      <spirit:modelParameter xsi:type="spirit:nameValueTypeType" spirit:dataType="integer">
        <spirit:name>ADD_BUS_SIZE</spirit:name>
        <spirit:displayName>Add Bus Size</spirit:displayName>
        <spirit:value spirit:format="long" spirit:resolve="generated" spirit:id="MODELPARAM_VALUE.ADD_BUS_SIZE">16</spirit:value>
      </spirit:modelParameter>
      <spirit:modelParameter spirit:dataType="integer">
        <spirit:name>ADD_ALIGNEMENT</spirit:name>
        <spirit:displayName>Add Alignement</spirit:displayName>
        <spirit:value spirit:format="long" spirit:resolve="generated" spirit:id="MODELPARAM_VALUE.ADD_ALIGNEMENT">4</spirit:value>
      </spirit:modelParameter>
      <spirit:modelParameter spirit:dataType="integer">
        <spirit:name>ADD_W_START</spirit:name>
        <spirit:displayName>Add W Start</spirit:displayName>
        <spirit:value spirit:format="long" spirit:resolve="generated" spirit:id="MODELPARAM_VALUE.ADD_W_START">768</spirit:value>
      </spirit:modelParameter>
      <spirit:modelParameter spirit:dataType="integer">
        <spirit:name>ADD_R_START</spirit:name>
        <spirit:displayName>Add R Start</spirit:displayName>
        <spirit:value spirit:format="long" spirit:resolve="generated" spirit:id="MODELPARAM_VALUE.ADD_R_START">908</spirit:value>
      </spirit:modelParameter>
    </spirit:modelParameters>
  </spirit:model>
  <spirit:choices>
    <spirit:choice>
      <spirit:name>choice_list_9d8b0d81</spirit:name>
      <spirit:enumeration>ACTIVE_HIGH</spirit:enumeration>
      <spirit:enumeration>ACTIVE_LOW</spirit:enumeration>
    </spirit:choice>
  </spirit:choices>
  <spirit:fileSets>
    <spirit:fileSet>
      <spirit:name>xilinx_anylanguagesynthesis_view_fileset</spirit:name>
      <spirit:file>
        <spirit:name>src/%(pi)s</spirit:name>
        <spirit:fileType>vhdlSource</spirit:fileType>
        <spirit:userFileType>IMPORTED_FILE</spirit:userFileType>
      </spirit:file>
      <spirit:file>
        <spirit:name>src/TASTE2.vhd</spirit:name>
        <spirit:fileType>vhdlSource</spirit:fileType>
        <spirit:userFileType>CHECKSUM_9ba54baf</spirit:userFileType>
        <spirit:userFileType>IMPORTED_FILE</spirit:userFileType>
      </spirit:file>
    </spirit:fileSet>
    <spirit:fileSet>
      <spirit:name>xilinx_anylanguagebehavioralsimulation_view_fileset</spirit:name>
      <spirit:file>
        <spirit:name>src/%(pi)s</spirit:name>
        <spirit:fileType>vhdlSource</spirit:fileType>
        <spirit:userFileType>IMPORTED_FILE</spirit:userFileType>
      </spirit:file>
      <spirit:file>
        <spirit:name>src/TASTE2.vhd</spirit:name>
        <spirit:fileType>vhdlSource</spirit:fileType>
        <spirit:userFileType>IMPORTED_FILE</spirit:userFileType>
      </spirit:file>
    </spirit:fileSet>
    <spirit:fileSet>
      <spirit:name>xilinx_xpgui_view_fileset</spirit:name>
      <spirit:file>
        <spirit:name>xgui/TASTE_v1_0.tcl</spirit:name>
        <spirit:fileType>tclSource</spirit:fileType>
        <spirit:userFileType>CHECKSUM_1c7a8e6b</spirit:userFileType>
        <spirit:userFileType>XGUI_VERSION_2</spirit:userFileType>
      </spirit:file>
    </spirit:fileSet>
  </spirit:fileSets>
  <spirit:description>TASTE_v1_0</spirit:description>
  <spirit:parameters>
    <spirit:parameter>
      <spirit:name>ADD_BUS_SIZE</spirit:name>
      <spirit:displayName>Add Bus Size</spirit:displayName>
      <spirit:value spirit:format="long" spirit:resolve="user" spirit:id="PARAM_VALUE.ADD_BUS_SIZE">16</spirit:value>
    </spirit:parameter>
    <spirit:parameter>
      <spirit:name>ADD_ALIGNEMENT</spirit:name>
      <spirit:displayName>Add Alignement</spirit:displayName>
      <spirit:value spirit:format="long" spirit:resolve="user" spirit:id="PARAM_VALUE.ADD_ALIGNEMENT">4</spirit:value>
    </spirit:parameter>
    <spirit:parameter>
      <spirit:name>ADD_W_START</spirit:name>
      <spirit:displayName>Add W Start</spirit:displayName>
      <spirit:value spirit:format="long" spirit:resolve="user" spirit:id="PARAM_VALUE.ADD_W_START">768</spirit:value>
    </spirit:parameter>
    <spirit:parameter>
      <spirit:name>ADD_R_START</spirit:name>
      <spirit:displayName>Add R Start</spirit:displayName>
      <spirit:value spirit:format="long" spirit:resolve="user" spirit:id="PARAM_VALUE.ADD_R_START">908</spirit:value>
    </spirit:parameter>
    <spirit:parameter>
      <spirit:name>Component_Name</spirit:name>
      <spirit:value spirit:resolve="user" spirit:id="PARAM_VALUE.Component_Name" spirit:order="1">TASTE_v1_0</spirit:value>
    </spirit:parameter>
  </spirit:parameters>
  <spirit:vendorExtensions>
    <xilinx:coreExtensions>
      <xilinx:supportedFamilies>
        <xilinx:family xilinx:lifeCycle="Production">virtex7</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">qvirtex7</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">kintex7</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">kintex7l</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">qkintex7</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">qkintex7l</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">artix7</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">artix7l</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">aartix7</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">qartix7</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">zynq</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">qzynq</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">azynq</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">spartan7</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">aspartan7</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">virtexu</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">zynquplus</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">virtexuplus</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">virtexuplusHBM</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">kintexuplus</xilinx:family>
        <xilinx:family xilinx:lifeCycle="Production">kintexu</xilinx:family>
      </xilinx:supportedFamilies>
      <xilinx:taxonomies>
        <xilinx:taxonomy>/UserIP</xilinx:taxonomy>
      </xilinx:taxonomies>
      <xilinx:displayName>TASTE_v1_0</xilinx:displayName>
      <xilinx:definitionSource>package_project</xilinx:definitionSource>
      <xilinx:coreRevision>2</xilinx:coreRevision>
      <xilinx:coreCreationDateTime>2019-11-06T16:55:24Z</xilinx:coreCreationDateTime>
      <xilinx:tags>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@7841b94_ARCHIVE_LOCATION">/media/sf_C_DRIVE/Users/ViSOS/Desktop/rdto/TASTE/TASTE2/ip</xilinx:tag>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@65a9ef71_ARCHIVE_LOCATION">/media/sf_C_DRIVE/Users/ViSOS/Desktop/rdto/TASTE/TASTE2/ip</xilinx:tag>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@33eb4ed4_ARCHIVE_LOCATION">/media/sf_C_DRIVE/Users/ViSOS/Desktop/rdto/TASTE/TASTE2/ip</xilinx:tag>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@a4f28fd_ARCHIVE_LOCATION">/media/sf_C_DRIVE/Users/ViSOS/Desktop/rdto/TASTE/TASTE2/ip</xilinx:tag>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@2b3bc834_ARCHIVE_LOCATION">/media/sf_C_DRIVE/Users/ViSOS/Desktop/rdto/TASTE/TASTE2/ip</xilinx:tag>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@368e1623_ARCHIVE_LOCATION">/media/sf_C_DRIVE/Users/ViSOS/Desktop/rdto/TASTE/TASTE2/ip</xilinx:tag>
      </xilinx:tags>
    </xilinx:coreExtensions>
    <xilinx:packagingInfo>
      <xilinx:xilinxVersion>2018.3</xilinx:xilinxVersion>
      <xilinx:checksum xilinx:scope="busInterfaces" xilinx:value="da618e65"/>
      <xilinx:checksum xilinx:scope="memoryMaps" xilinx:value="5ccc3619"/>
      <xilinx:checksum xilinx:scope="fileGroups" xilinx:value="99da1e43"/>
      <xilinx:checksum xilinx:scope="ports" xilinx:value="f2458798"/>
      <xilinx:checksum xilinx:scope="hdlParameters" xilinx:value="51897e61"/>
      <xilinx:checksum xilinx:scope="parameters" xilinx:value="104060ee"/>
    </xilinx:packagingInfo>
  </spirit:vendorExtensions>
</spirit:component>"""
