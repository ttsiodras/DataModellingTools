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
-- Create Date: 01/04/2020
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
    port (
		---------------------------------------------------
		--			  	AXI4 LITE (REGISTERS)		 	 --
		---------------------------------------------------
		-- Clock and Reset
		S00_AXI_ACLK			: in  std_logic;
		S00_AXI_ARESETN			: in  std_logic;
		-- Write Address Channel
		S00_AXI_AWADDR			: in  std_logic_vector(31 downto 0);
		S00_AXI_AWVALID			: in  std_logic;
		S00_AXI_AWREADY			: out std_logic;
		-- Write Data Channel
		S00_AXI_WDATA			: in  std_logic_vector(31 downto 0);
		S00_AXI_WSTRB			: in  std_logic_vector(3 downto 0);
		S00_AXI_WVALID			: in  std_logic;
		S00_AXI_WREADY			: out std_logic;
		-- Read Address Channel
		S00_AXI_ARADDR			: in  std_logic_vector(31 downto 0);
		S00_AXI_ARVALID			: in  std_logic;
		S00_AXI_ARREADY			: out std_logic;
		-- Read Data Channel
		S00_AXI_RDATA			: out std_logic_vector(31 downto 0);
		S00_AXI_RRESP			: out std_logic_vector(1 downto 0);
		S00_AXI_RVALID			: out std_logic;
		S00_AXI_RREADY			: in  std_logic;
		-- Write Response Channel
		S00_AXI_BRESP			: out std_logic_vector(1 downto 0);
		S00_AXI_BVALID			: out std_logic;
		S00_AXI_BREADY			: in  std_logic;
		---------------------------------------------------
		--			  AXI4 LITE (DDR CONTROLLER)		 --
		---------------------------------------------------
		-- Clock and Reset
		M00_AXI_ACLK			: in  std_logic;
		M00_AXI_ARESETN			: in  std_logic;
		-- Write Address Channel
		M00_AXI_AWADDR  		: out std_logic_vector(31 downto 0);
		M00_AXI_AWVALID 		: out std_logic;
		M00_AXI_AWREADY 		: in  std_logic;
		-- Write Data Channel
		M00_AXI_WDATA   		: out std_logic_vector(63 downto 0);
		M00_AXI_WSTRB   		: out std_logic_vector(7 downto 0);
		M00_AXI_WVALID  		: out std_logic;
		M00_AXI_WREADY  		: in  std_logic;
		-- Read Address Channel
		M00_AXI_ARADDR  		: out std_logic_vector(31 downto 0);
		M00_AXI_ARVALID 		: out std_logic;
		M00_AXI_ARREADY 		: in  std_logic;
		-- Read Data Channel
		M00_AXI_RDATA   		: in  std_logic_vector(63 downto 0);
		M00_AXI_RRESP   		: in  std_logic_vector(1 downto 0);
		M00_AXI_RVALID  		: in  std_logic;
		M00_AXI_RREADY  		: out std_logic;
		-- Write Response Channel
		M00_AXI_BRESP   		: in  std_logic_vector(1 downto 0);
		M00_AXI_BVALID  		: in  std_logic;
		M00_AXI_BREADY  		: out std_logic;
		---------------------------------------------------
		--			  	   AXI4 LITE (BRAMs)		 	 --
		---------------------------------------------------
		-- Clock and Reset
		S01_AXI_ACLK			: in  std_logic;
		S01_AXI_ARESETN			: in  std_logic;
		-- Write Address Channel
		S01_AXI_AWADDR			: in  std_logic_vector(31 downto 0);
		S01_AXI_AWVALID			: in  std_logic;
		S01_AXI_AWREADY			: out std_logic;
		-- Write Data Channel
		S01_AXI_WDATA			: in  std_logic_vector(31 downto 0);
		S01_AXI_WSTRB			: in  std_logic_vector(3 downto 0);
		S01_AXI_WVALID			: in  std_logic;
		S01_AXI_WREADY			: out std_logic;
		-- Read Address Channel
		S01_AXI_ARADDR			: in  std_logic_vector(31 downto 0);
		S01_AXI_ARVALID			: in  std_logic;
		S01_AXI_ARREADY			: out std_logic;
		-- Read Data Channel
		S01_AXI_RDATA			: out std_logic_vector(31 downto 0);
		S01_AXI_RRESP			: out std_logic_vector(1 downto 0);
		S01_AXI_RVALID			: out std_logic;
		S01_AXI_RREADY			: in  std_logic;
		-- Write Response Channel
		S01_AXI_BRESP			: out std_logic_vector(1 downto 0);
		S01_AXI_BVALID			: out std_logic;
		S01_AXI_BREADY			: in  std_logic;
		---------------------------------------------------
		--	   AXI4 STREAM SLAVE DATA SIGNALS (FIFOs) 	 --
		---------------------------------------------------
		-- Clock and Reset
		S00_AXIS_ACLK    		: in  std_logic;
		S00_AXIS_ARESETN 		: in  std_logic;
		-- Data Channel		
		S00_AXIS_TVALID 		: in  std_logic;
		S00_AXIS_TREADY 		: out std_logic;
		S00_AXIS_TDATA  		: in  std_logic_vector(31 downto 0);
		S00_AXIS_TLAST 			: in  std_logic;
		S00_AXIS_TDEST			: in  std_logic_vector(4 downto 0);
		---------------------------------------------------
		--	  AXI4 STREAM MASTER DATA SIGNALS (FIFOs) 	 --
		---------------------------------------------------
		-- Clock and Reset
		M00_AXIS_ACLK    		: in  std_logic;
		M00_AXIS_ARESETN 		: in  std_logic;
		-- Data Channel		
		M00_AXIS_TVALID 		: out std_logic;
		M00_AXIS_TREADY 		: in  std_logic;
		M00_AXIS_TDATA  		: out std_logic_vector(31 downto 0);
		M00_AXIS_TLAST 			: out std_logic;
		M00_AXIS_TID			: out std_logic_vector(4 downto 0)
    );
end TASTE;

architecture rtl of TASTE is

	---------------------------------------------------
	--			  COMPONENT DECLARATION			 	 --
	---------------------------------------------------	
    -- Circuits for the existing PIs
%(circuits)s

	---------------------------------------------------
	--			  CONSTANTS			 	 	 		 --
	---------------------------------------------------
	
	constant OKAY						: std_logic_vector(1 downto 0) 		:= "00";
	constant EXOKAY						: std_logic_vector(1 downto 0) 		:= "01";
	constant SLVERR						: std_logic_vector(1 downto 0) 		:= "10";
	constant DECERR						: std_logic_vector(1 downto 0) 		:= "11";
	constant S2MM_PACKET_SIZE			: integer							:= 1024;


	----------------------------------------------------
	--			  	TYPE DEFINITION			 	 	  --
	----------------------------------------------------

	------------------------------
	--	        S00 AXI	    	--
	------------------------------
	type S00_AXI_states is(idle, reading, r_complete, writing, wait_resp);
	
	type S00_AXI_comb_out is record		

		awready			: std_logic;
		wready			: std_logic;
		arready			: std_logic;
		rdata			: std_logic_vector(31 downto 0);
		rresp			: std_logic_vector(1 downto 0);
		rvalid			: std_logic;
		bvalid			: std_logic;
	
	end record;
	
	-- AXI4 internal signals record --
	type S00_AXI_inter is record
	
		axi_state			: S00_AXI_states;
		r_local_address			: integer;
		bresp					: std_logic_vector(1 downto 0);
        --Registers for I/O
        %(s00_signals_declaration)s
        ddr_ext_pointer_A				: std_logic_vector(31 downto 0);
		startInternal					: std_logic;
		startInternalOld				: std_logic;
		doneInternal					: std_logic;
	
	end record;
	
	constant INIT_S00_AXI_COMB_OUT	                : S00_AXI_comb_out	:= (awready		=> '0',	
																			wready		=> '0',
																			arready		=> '0',
																			rdata		=> (others => '0'),
																			rresp		=> OKAY,
																			rvalid		=> '0',
																			bvalid		=> '0'
																			);
																						
	constant INIT_S00_AXI_INTER	                   : S00_AXI_inter 		:= (axi_state		=> idle,
                                                                            r_local_address		=> 0,
                                                                            bresp				=> OKAY,
                                                                            --Registers for I/O
                                                                            %(s00_signals_assign)s
                                                                            ddr_ext_pointer_A	=> (others => '0'),
                                                                            startInternal		=> '0',		
                                                                            startInternalOld	=> '0',
                                                                            doneInternal		=> '0'
                                                                            );
	
	------------------------------
	--	        S01 AXI	    	--
	------------------------------
	type S01_AXI_states is(idle, reading, r_complete, writing, wait_resp);
	
	type S01_AXI_comb_out is record		

		awready			: std_logic;
		wready			: std_logic;
		arready			: std_logic;
		rdata			: std_logic_vector(31 downto 0);
		rresp			: std_logic_vector(1 downto 0);
		rvalid			: std_logic;
		bvalid			: std_logic;
        %(s01_signals_declaration)s
        
	end record;
	
	-- AXI4 internal signals record --
	type S01_AXI_inter is record
	
		axi_state			: S01_AXI_states;
		r_local_address			: integer;
		bresp					: std_logic_vector(1 downto 0);
	
	end record;
	
	constant INIT_S01_AXI_COMB_OUT	                : S01_AXI_comb_out	:= (%(s01_signals_assign)s
                                                                            awready		=> '0',	
																			wready		=> '0',
																			arready		=> '0',
																			rdata		=> (others => '0'),
																			rresp		=> OKAY,
																			rvalid		=> '0',
																			bvalid		=> '0'
																			);
																						
	constant INIT_S01_AXI_INTER	                   : S01_AXI_inter 		:= (axi_state		=> idle,
                                                                            r_local_address		=> 0,
                                                                            bresp				=> OKAY
                                                                            );
	
														
	---------------------------------------------------
	--			  		  M00 AXI		 	 		 --
	---------------------------------------------------
	type M00_AXI_states is(idle, writing, writing_finish, reading);
	
	type M00_AXI_comb_out is record		

		awaddr  						: std_logic_vector(31 downto 0);
		awvalid 						: std_logic;
		wdata   						: std_logic_vector(63 downto 0);
		wstrb   						: std_logic_vector(7 downto 0);
		wvalid  						: std_logic;
		araddr  						: std_logic_vector(31 downto 0);
		arvalid 						: std_logic;
		rready  						: std_logic;
		bready  						: std_logic;
		%(m00_signals_declaration)s
	
	end record;
	
	-- AXI4 internal signals record --
	type M00_AXI_inter is record
	
		axi_state						: M00_AXI_states;
		
	end record;
	
	constant INIT_M00_AXI_COMB_OUT		: M00_AXI_comb_out		:= (%(m00_signals_assign)s
                                                                    awaddr 				=> (others => '0'),
																	awvalid				=> '0',
																	wdata  				=> (others => '0'),
																	wstrb  				=> (others => '0'),
																	wvalid 				=> '0',
																	araddr 				=> (others => '0'),
																	arvalid				=> '0',
																	rready 				=> '0',
																	bready 				=> '0'
																	);
																						
	constant INIT_M00_AXI_INTER			: M00_AXI_inter 		:= (axi_state			=> idle
																	);
																	
	---------------------------------------------------
	--			  		  S00 AXIS		 	 		 --
	---------------------------------------------------
	type S00_AXIS_states is(idle, runing);	
	
	type S00_AXIS_comb_out is record		

		tready							: std_logic;
		%(s00s_signals_declaration)s
	
	end record;
	
	type S00_AXIS_inter is record		

		axis_state						: S00_AXIS_states;
	
	end record;
	
	constant INIT_S00_AXIS_COMB_OUT		: S00_AXIS_comb_out 	:= (%(s00s_signals_assign)s
                                                                    tready				=> '0'
                                                                    );		
	
	constant INIT_S00_AXIS_INTER		: S00_AXIS_inter 		:= (axis_state			=> idle);

	---------------------------------------------------
	--			  		  M00 AXIS		 	 		 --
	---------------------------------------------------
	type M00_AXIS_states is(idle, runing);

	type M00_AXIS_comb_out is record		

		tvalid							: std_logic;
		tdata							: std_logic_vector(31 downto 0);
		tlast							: std_logic;
		%(m00s_signals_declaration)s
	
	end record;
	
	type M00_AXIS_inter is record		

		axis_state						: M00_AXIS_states;
		current_tid						: std_logic_vector(4 downto 0);
		data_counter					: std_logic_vector(23 downto 0);
		fifo_empty_vector				: std_logic_vector(31 downto 0);
	
	end record;

	constant INIT_M00_AXIS_COMB_OUT		: M00_AXIS_comb_out 	:= (%(m00s_signals_assign)s
                                                                    tvalid				=> '0',
																	tdata				=> (others => '0'),
																	tlast				=> '0'
																	);	
	
	constant INIT_M00_AXIS_INTER		: M00_AXIS_inter 		:= (axis_state			=> idle,
																	current_tid			=> (others => '0'),
																	data_counter		=> (others => '0'),
																	fifo_empty_vector	=> (others => '1')
																	);
	------------------------------
	--	SIGNAL DECLARATION		--
	------------------------------	
    -- Registers for I/O
    %(ioregisters)s

	-- AXI LITE SLAVE Registers Signals --	
	signal S00_AXI_r					: S00_AXI_inter;
	signal S00_AXI_rin					: S00_AXI_inter;
	signal S00_AXI_r_comb_out			: S00_AXI_comb_out;
	signal S00_AXI_rin_comb_out			: S00_AXI_comb_out;
	-- AXI LITE MASTER AXI DDR3 Signals --	
	signal M00_AXI_r					: M00_AXI_inter;
	signal M00_AXI_rin					: M00_AXI_inter;
	signal M00_AXI_r_comb_out			: M00_AXI_comb_out;
	signal M00_AXI_rin_comb_out			: M00_AXI_comb_out;
	-- AXI LITE SLAVE BRAM Signals --	
	signal S01_AXI_r					: S01_AXI_inter;
	signal S01_AXI_rin					: S01_AXI_inter;
	signal S01_AXI_r_comb_out			: S01_AXI_comb_out;
	signal S01_AXI_rin_comb_out			: S01_AXI_comb_out;	
	-- AXI STREAM SLAVE FIFOs Signals --	
	signal S00_AXIS_r					: S00_AXIS_inter;
	signal S00_AXIS_rin					: S00_AXIS_inter;
	signal S00_AXIS_r_comb_out			: S00_AXIS_comb_out;
	signal S00_AXIS_rin_comb_out		: S00_AXIS_comb_out;
	-- AXI STREAM MASTER FIFOs Signals --	
	signal M00_AXIS_r					: M00_AXIS_inter;
	signal M00_AXIS_rin					: M00_AXIS_inter;
	signal M00_AXIS_r_comb_out			: M00_AXIS_comb_out;
	signal M00_AXIS_rin_comb_out		: M00_AXIS_comb_out;
begin

	---------------------------------------------------
	--				COMPONENT INSTANTITATION		 --
	---------------------------------------------------
    -- Connections to the VHDL circuits
%(connectionsToSystemC)s

%(connectionsToBRAMs)s

%(connectionsToFIFOs)s


	---------------------------------------------------
	--				PROCESS INSTANTIATION		     --
	---------------------------------------------------		
	
	------------------------------------------------------------------------------------------
	--                                       S00 AXI                                        --
	------------------------------------------------------------------------------------------
	-- Sequential process --
	seq_axi_slave:	process(S00_AXI_ACLK)
	begin 		
		if rising_edge(S00_AXI_ACLK) then
			S00_AXI_r				<= S00_AXI_rin;
			S00_AXI_r_comb_out		<= S00_AXI_rin_comb_out;
		end if;
	end process;

	-- Combinational process --	
	comb_axi_slave: process(-- Bambu signals --
							%(s00_signals)s
							-- internal signals --
							S00_AXI_r, S00_AXI_r_comb_out,
							-- AXI inptuts --
							S00_AXI_ARESETN, S00_AXI_AWADDR, S00_AXI_AWVALID, S00_AXI_WDATA, S00_AXI_WSTRB, S00_AXI_WVALID, S00_AXI_ARADDR, S00_AXI_ARVALID, S00_AXI_RREADY, S00_AXI_BREADY
							)
							
		variable v										: S00_AXI_inter;
		variable v_comb_out								: S00_AXI_comb_out;
		variable comb_S00_AXI_AWVALID_S00_AXI_ARVALID	: std_logic_vector(1 downto 0);
		variable w_local_address						: integer;
		
	begin
	
		-----------------------------------------------------------------
		--				   DEFAULT VARIABLES ASIGNATION		           --
		-----------------------------------------------------------------
		v 											:= S00_AXI_r;		
		-----------------------------------------------------------------
		--	 	DEFAULT COMBINATIONAL OUTPUT VARIABLES ASIGNATION      --
		-----------------------------------------------------------------
		v_comb_out									:= INIT_S00_AXI_COMB_OUT;
		if %(starts)s = '1' then
			v.doneInternal							:= '0';
		end if;
		if %(completions)s = '1' then
			v.doneInternal							:= '1';
		end if;
		-----------------------------------------------------------------
		--	 			DEFAULT INTERNAL VARIABLE ASIGNATION      	   --
		-----------------------------------------------------------------		
		w_local_address								:= to_integer(unsigned(S00_AXI_AWADDR(15 downto 0)));
		comb_S00_AXI_AWVALID_S00_AXI_ARVALID		:= S00_AXI_AWVALID&S00_AXI_ARVALID;	
		-- Update start-stop pulses
		v.startInternalOld 							:= S00_AXI_r.startInternal;
                -----------------------------------------------------------------
		--	 					 AXI LITE CTRL FSM      	   		   --
		-----------------------------------------------------------------		
		case S00_AXI_r.axi_state is
			when idle =>
				v.bresp								:= OKAY;
				case comb_S00_AXI_AWVALID_S00_AXI_ARVALID is
					when "01" 	=> 
						v.axi_state 				:= reading;
					when "11" 	=> 
						v.axi_state 				:= reading;
					when "10" 	=> 
						v.axi_state 				:= writing;
					when others	=> 
						v.axi_state 				:= idle;
				end case;		
			
			when writing =>
				v_comb_out.awready					:= S00_AXI_AWVALID;
				v_comb_out.wready					:= S00_AXI_WVALID;
				v.bresp								:= S00_AXI_r.bresp;				
				if S00_AXI_WVALID = '1' then
					v.axi_state	:= wait_resp;
					case w_local_address is
                        when (0) 					=> v.startInternal				:= S00_AXI_r.startInternal xor '1';
                        %(s00_signals_writing)s
						when others => null;
					end case;
				end if;
				
			when wait_resp =>
				v_comb_out.awready					:= S00_AXI_AWVALID;
				v_comb_out.wready					:= S00_AXI_WVALID;
				v.bresp								:= S00_AXI_r.bresp;
				v_comb_out.bvalid					:= S00_AXI_BREADY;
				if S00_AXI_AWVALID = '0' then
					v.axi_state 					:= idle;
				else
					if S00_AXI_WVALID = '1' then
						case w_local_address is
							when (0) 				=> v.startInternal				:= S00_AXI_r.startInternal xor '1';
                        %(s00_signals_writing)s
							when others => null;
						end case;
					else
						v.axi_state := writing;
					end if;
				end if;
			
			when reading =>
				v_comb_out.arready					:= S00_AXI_ARVALID;
				v.bresp								:= OKAY;
				v.r_local_address					:= to_integer(unsigned(S00_AXI_ARADDR(15 downto 0)));
				v.axi_state 						:= r_complete;
			when r_complete => 
				v_comb_out.arready					:= S00_AXI_ARVALID;
				v_comb_out.rvalid					:= '1';
				v.bresp								:= OKAY;
				if S00_AXI_RREADY = '1' then
					if S00_AXI_ARVALID = '0' then
						v.axi_state 				:= idle;
					else
						v.r_local_address			:= to_integer(unsigned(S00_AXI_ARADDR(15 downto 0)));
					end if;
				end if;
				case S00_AXI_r.r_local_address is
					-- result calculated flag 
					when (0) 						=> v_comb_out.rdata(31 downto 0) := X"000000"&"0000000"&S00_AXI_r.doneInternal;
                    %(s00_signals_rcomp)s
					when others => v_comb_out.rdata(31 downto 0) 	:= (others => '0');								
				end case;
		end case;
		---------------------------------------------------
		--				  RESET ASIGNATION		 	     --
		---------------------------------------------------		
		if S00_AXI_ARESETN = '0' then
			v		    		:= INIT_S00_AXI_INTER;
			v_comb_out			:= INIT_S00_AXI_COMB_OUT;
		end if;
		---------------------------------------------------
		--				SIGNAL ASIGNATION			     --
		---------------------------------------------------
		S00_AXI_rin 	       	<= v;
		S00_AXI_rin_comb_out	<= v_comb_out;
		
	end process;


	---------------------------------------------------
	--		   INTERNAL ARCHITECTURE SIGNALS	 	 --
	---------------------------------------------------
        %(s00_signals_internal)s	

	---------------------------------------------------
	--					 OUTPUTS			 	     --
	---------------------------------------------------		
	S00_AXI_AWREADY				<= S00_AXI_rin_comb_out.awready;
	S00_AXI_WREADY				<= S00_AXI_rin_comb_out.wready;
	S00_AXI_ARREADY				<= S00_AXI_rin_comb_out.arready;
	S00_AXI_RDATA				<= S00_AXI_rin_comb_out.rdata;
	S00_AXI_RRESP				<= S00_AXI_rin_comb_out.rresp;
	S00_AXI_RVALID				<= S00_AXI_rin_comb_out.rvalid;
	S00_AXI_BRESP				<= S00_AXI_rin.bresp;
	S00_AXI_BVALID				<= S00_AXI_rin_comb_out.bvalid;
	
		------------------------------------------------------------------------------------------
	--                                       M00 AXI                                        --
	------------------------------------------------------------------------------------------
	-- Sequential process --
	m00_axi_seq: process(M00_AXI_ACLK)
	begin 		
		if rising_edge(M00_AXI_ACLK) then
			M00_AXI_r				<= M00_AXI_rin;
			M00_AXI_r_comb_out		<= M00_AXI_rin_comb_out;
		end if;
	end process;

	-- Combinational process --	
	m00_axi_comb: process(	%(m00_signals)s
                            -- internal signals --
							M00_AXI_r, M00_AXI_r_comb_out,
							-- AXI inptuts --
							M00_AXI_AWREADY, M00_AXI_WREADY, M00_AXI_ARREADY, M00_AXI_RDATA, M00_AXI_RRESP, M00_AXI_RVALID, M00_AXI_BRESP, M00_AXI_BVALID
							)
							
		variable v										: M00_AXI_inter;
		variable v_comb_out								: M00_AXI_comb_out;
		variable comb_Mout_we_ram_Mout_oe_ram			: std_logic_vector(1 downto 0);
		variable comb_m_axi_awready_comb_m_axi_wready	: std_logic_vector(1 downto 0);
		
	begin
	
		-----------------------------------------------------------------
		--				   DEFAULT VARIABLES ASIGNATION		           --
		-----------------------------------------------------------------
		v 											:= M00_AXI_r;		
		-----------------------------------------------------------------
		--	 	DEFAULT COMBINATIONAL OUTPUT VARIABLES ASIGNATION      --
		-----------------------------------------------------------------
		v_comb_out									:= INIT_M00_AXI_COMB_OUT;
		-----------------------------------------------------------------
		--	 			DEFAULT INTERNAL VARIABLE ASIGNATION      	   --
		-----------------------------------------------------------------
		%(m00_signals_internalassign)s
		v_comb_out.M_Rdata_ram						:= M00_AXI_RDATA;
		comb_m_axi_awready_comb_m_axi_wready		:= M00_AXI_AWREADY&M00_AXI_WREADY;
		v_comb_out.wstrb							:= (others => '1');
		-----------------------------------------------------------------
		--	 					 AXI LITE CTRL FSM      	   		   --
		-----------------------------------------------------------------		
		case M00_AXI_r.axi_state is
			when idle =>
				case comb_Mout_we_ram_Mout_oe_ram is
					when "01" 	=> 
						v_comb_out.arvalid			:= '1';
						v_comb_out.rready			:= '1';
						if M00_AXI_ARREADY = '1' then
							v.axi_state 			:= reading;
						end if;
					when "11" 	=> 
						v_comb_out.arvalid			:= '1';
						if M00_AXI_ARREADY = '1' then
							v.axi_state 			:= reading;
						end if;
					when "10" 	=> 
						v_comb_out.awvalid			:= '1';
						v_comb_out.wvalid			:= '1';
						case comb_m_axi_awready_comb_m_axi_wready is
							when "11" =>
								v.axi_state 		:= writing_finish;
							when "10" =>
								v.axi_state 		:= writing;
							when others =>
								v.axi_state 		:= idle;
						end case; 
					when others	=> 
						v.axi_state 				:= idle;
				end case;			
			when writing =>
				v_comb_out.awvalid					:= '1';
				v_comb_out.wvalid					:= '1';
				case comb_m_axi_awready_comb_m_axi_wready is
					when "11" =>
						v.axi_state 				:= writing_finish;
					when "01" =>
						v.axi_state 				:= writing_finish;
					when others =>
						v.axi_state 				:= writing;
				end case; 	
			when writing_finish =>
				v_comb_out.bready					:= '1';
				if M00_AXI_BVALID = '1' then
					if M00_AXI_BRESP = OKAY then
						v_comb_out.M_DataRdy		:= '1';
					end if;
					v.axi_state 					:= idle;
				end if;		
			when reading =>
				v_comb_out.rready					:= '1';
				if M00_AXI_RVALID = '1' then
					if M00_AXI_RRESP = OKAY then
						v_comb_out.M_DataRdy		:= '1';
					end if;
					v.axi_state 					:= idle;
				end if;
		end case;
		---------------------------------------------------
		--				  RESET ASIGNATION		 	     --
		---------------------------------------------------		
		if M00_AXI_ARESETN = '0' then
			v		    		:= INIT_M00_AXI_INTER;
			v_comb_out			:= INIT_M00_AXI_COMB_OUT;
		end if;
		---------------------------------------------------
		--				SIGNAL ASIGNATION			     --
		---------------------------------------------------
		M00_AXI_rin 	       	<= v;
		M00_AXI_rin_comb_out	<= v_comb_out;
		
	end process;	
	
	---------------------------------------------------
	--		   INTERNAL ARCHITECTURE SIGNALS	 	 --
	---------------------------------------------------
	%(m00_signals_internal)s
	
	---------------------------------------------------
	--					 OUTPUTS			 	     --
	---------------------------------------------------		
	M00_AXI_AWADDR				<= M00_AXI_rin_comb_out.awaddr;
	M00_AXI_AWVALID				<= M00_AXI_rin_comb_out.awvalid;
	M00_AXI_WDATA				<= M00_AXI_rin_comb_out.wdata;
	M00_AXI_WSTRB				<= M00_AXI_rin_comb_out.wstrb;
	M00_AXI_WVALID				<= M00_AXI_rin_comb_out.wvalid;
	M00_AXI_ARADDR				<= M00_AXI_rin_comb_out.araddr;
	M00_AXI_ARVALID				<= M00_AXI_rin_comb_out.arvalid;
	M00_AXI_RREADY				<= M00_AXI_rin_comb_out.rready;
	M00_AXI_BREADY				<= M00_AXI_rin_comb_out.bready;
	
	------------------------------------------------------------------------------------------
	--                                       S01 AXI                                        --
	------------------------------------------------------------------------------------------
	-- Sequential process --
	s01_axi_seq: process(S01_AXI_ACLK)
	begin 		
		if rising_edge(S01_AXI_ACLK) then
			S01_AXI_r				<= S01_AXI_rin;
			S01_AXI_r_comb_out		<= S01_AXI_rin_comb_out;
		end if;
	end process;

	-- Combinational process --	
	s01_axi_comb: process(	-- Bambu signals --
                            %(s01_signals)s
                            -- internal signals --
							S01_AXI_r, S01_AXI_r_comb_out,
							-- AXI inptuts --
							S01_AXI_ARESETN, S01_AXI_AWADDR, S01_AXI_AWVALID, S01_AXI_WDATA, S01_AXI_WSTRB, S01_AXI_WVALID, S01_AXI_ARADDR, S01_AXI_ARVALID, S01_AXI_RREADY, S01_AXI_BREADY
							)
							
		variable v										: S01_AXI_inter;
		variable v_comb_out								: S01_AXI_comb_out;
		variable comb_S01_AXI_AWVALID_S01_AXI_ARVALID	: std_logic_vector(1 downto 0);
		variable w_local_address						: integer;

	begin
	
		-----------------------------------------------------------------
		--				   DEFAULT VARIABLES ASIGNATION		           --
		-----------------------------------------------------------------
		v 											:= S01_AXI_r;		
		-----------------------------------------------------------------
		--	 	DEFAULT COMBINATIONAL OUTPUT VARIABLES ASIGNATION      --
		-----------------------------------------------------------------
		v_comb_out									:= INIT_S01_AXI_COMB_OUT;
		-----------------------------------------------------------------
		--	 			DEFAULT INTERNAL VARIABLE ASIGNATION      	   --
		-----------------------------------------------------------------		
		w_local_address								:= to_integer(unsigned(S01_AXI_AWADDR(23 downto 22)));
		comb_S01_AXI_AWVALID_S01_AXI_ARVALID		:= S01_AXI_AWVALID&S01_AXI_ARVALID;	
		-----------------------------------------------------------------
		--	 					 AXI LITE CTRL FSM      	   		   --
		-----------------------------------------------------------------		
		case S01_AXI_r.axi_state is
			when idle =>
				v.bresp								:= OKAY;
				case comb_S01_AXI_AWVALID_S01_AXI_ARVALID is
					when "01" 	=> 
						v.axi_state 				:= reading;
					when "11" 	=> 
						v.axi_state 				:= reading;
					when "10" 	=> 
						v.axi_state 				:= writing;
					when others	=> 
						v.axi_state 				:= idle;
				end case;			
			when writing =>
				v_comb_out.awready					:= S01_AXI_AWVALID;
				v_comb_out.wready					:= S01_AXI_WVALID;
				v.bresp								:= S01_AXI_r.bresp;				
				if S01_AXI_WVALID = '1' then
					v.axi_state	:= wait_resp;
					case w_local_address is
						%(s01_signals_write)s
						when others => null;
					end case;
				end if;		
			when wait_resp =>
				v_comb_out.awready					:= S01_AXI_AWVALID;
				v_comb_out.wready					:= S01_AXI_WVALID;
				v.bresp								:= S01_AXI_r.bresp;
				v_comb_out.bvalid					:= S01_AXI_BREADY;
				if S01_AXI_AWVALID = '0' then
					v.axi_state 					:= idle;
				else
					if S01_AXI_WVALID = '1' then
						case w_local_address is
						%(s01_signals_write)s
						when others => null;
						end case;
					else
						v.axi_state := writing;
					end if;
				end if;			
			when reading =>
				v_comb_out.arready					:= S01_AXI_ARVALID;
				v.bresp								:= OKAY;
				v.r_local_address					:= to_integer(unsigned(S01_AXI_ARADDR(23 downto 22)));
				v.axi_state 						:= r_complete;
				case v.r_local_address is
					%(s01_signals_read)s
					when others 					=> null;
				end case;
			when r_complete => 
				v_comb_out.arready					:= S01_AXI_ARVALID;
				v_comb_out.rvalid					:= '1';
				v.bresp								:= OKAY;
				if S01_AXI_RREADY = '1' then
					if S01_AXI_ARVALID = '0' then
						v.axi_state 				:= idle;
					else
						v.r_local_address			:= to_integer(unsigned(S01_AXI_ARADDR(23 downto 22)));
						case v.r_local_address is
							%(s01_signals_read)s
							when others 			=> null;
						end case;
					end if;
				end if;
				case S01_AXI_r.r_local_address is
					-- result calculated flag do_something2
					%(s01_signals_rcomp_res)s
					when others 					=> v_comb_out.rdata(31 downto 0) 	:= (others => '0');								
				end case;
		end case;
		---------------------------------------------------
		--				  RESET ASIGNATION		 	     --
		---------------------------------------------------		
		if S01_AXI_ARESETN = '0' then
			v		    		:= INIT_S01_AXI_INTER;
			v_comb_out			:= INIT_S01_AXI_COMB_OUT;
		end if;
		---------------------------------------------------
		--				SIGNAL ASIGNATION			     --
		---------------------------------------------------
		S01_AXI_rin 	       	<= v;
		S01_AXI_rin_comb_out	<= v_comb_out;
		
	end process;	
	
	---------------------------------------------------
	--		   INTERNAL ARCHITECTURE SIGNALS	 	 --
	---------------------------------------------------
    %(s01_signals_internal)s
	---------------------------------------------------
	--					 OUTPUTS			 	     --
	---------------------------------------------------		
	S01_AXI_AWREADY				<= S01_AXI_rin_comb_out.awready;
	S01_AXI_WREADY				<= S01_AXI_rin_comb_out.wready;
	S01_AXI_ARREADY				<= S01_AXI_rin_comb_out.arready;
	S01_AXI_RDATA				<= S01_AXI_rin_comb_out.rdata;
	S01_AXI_RRESP				<= S01_AXI_rin_comb_out.rresp;
	S01_AXI_RVALID				<= S01_AXI_rin_comb_out.rvalid;
	S01_AXI_BRESP				<= S01_AXI_rin.bresp;
	S01_AXI_BVALID				<= S01_AXI_rin_comb_out.bvalid;	
	
    ------------------------------------------------------------------------------------------
	--                                       S00 AXIS                                       --
	------------------------------------------------------------------------------------------
	-- Sequential process --
	s00_axis_seq: process(S00_AXIS_ACLK)
	begin 		
		if rising_edge(S00_AXIS_ACLK) then
			S00_AXIS_r				<= S00_AXIS_rin;
			S00_AXIS_r_comb_out		<= S00_AXIS_rin_comb_out;
		end if;
	end process;
	
	-- Combinational process --	
	s00_axis_comb: process(	-- Bambu signals --
							%(s00s_signals)s
							-- internal signals --
							S00_AXIS_r, S00_AXIS_r_comb_out,
							-- AXI inptuts --
							S00_AXIS_ARESETN, S00_AXIS_TVALID, S00_AXIS_TDATA, S00_AXIS_TLAST, S00_AXIS_TDEST							
							)
	
		variable v									: S00_AXIS_inter;
		variable v_comb_out							: S00_AXIS_comb_out;
		variable w_local_address					: integer;
		
	begin
	
		-----------------------------------------------------------------
		--				   DEFAULT VARIABLES ASIGNATION		           --
		-----------------------------------------------------------------
		v 											:= S00_AXIS_r;		
		-----------------------------------------------------------------
		--	 	DEFAULT COMBINATIONAL OUTPUT VARIABLES ASIGNATION      --
		-----------------------------------------------------------------
		v_comb_out									:= INIT_S00_AXIS_COMB_OUT;
		-----------------------------------------------------------------
		--	 			DEFAULT INTERNAL VARIABLE ASIGNATION      	   --
		-----------------------------------------------------------------		
		w_local_address								:= to_integer(unsigned(S00_AXIS_TDEST));		
		-----------------------------------------------------------------
		--	 					 AXIS SLAVE CTRL FSM      	   		   --
		-----------------------------------------------------------------
		case S00_AXIS_r.axis_state is
			when idle =>
				if S00_AXIS_TVALID = '1' then
					v.axis_state					:= runing;
				end if;
			when runing =>	
				case w_local_address is
					%(s00s_signals_running)s
					when others => null;
				end case;
				if S00_AXIS_TLAST = '1' then
					v.axis_state					:= idle;
				end if;
			when others => null;
		end case;		
		---------------------------------------------------
		--				  RESET ASIGNATION		 	     --
		---------------------------------------------------
		if S00_AXIS_ARESETN = '0' then
			v		    		:= INIT_S00_AXIS_INTER;
			v_comb_out			:= INIT_S00_AXIS_COMB_OUT;
		end if;
		---------------------------------------------------
		--				SIGNAL ASIGNATION			     --
		---------------------------------------------------
		S00_AXIS_rin 	       	<= v;
		S00_AXIS_rin_comb_out	<= v_comb_out;	
	
	end process;	
	
	---------------------------------------------------
	--		   INTERNAL ARCHITECTURE SIGNALS	 	 --
	---------------------------------------------------
    %(s00s_signals_internal)s
    
	---------------------------------------------------
	--					 OUTPUTS			 	     --
	---------------------------------------------------		
	S00_AXIS_TREADY				<= S00_AXIS_rin_comb_out.tready;		
	
	------------------------------------------------------------------------------------------
	--                                       M00 AXIS                                       --
	------------------------------------------------------------------------------------------	
	-- Sequential process --
	m00_axis_seq: process(M00_AXIS_ACLK)
	begin 		
		if rising_edge(M00_AXIS_ACLK) then
			M00_AXIS_r				<= M00_AXIS_rin;
			M00_AXIS_r_comb_out		<= M00_AXIS_rin_comb_out;
		end if;
	end process;
	
	-- Combinational process --	
	m00_axis_comb: process(	-- Bambu signals --
							%(m00s_signals)s
							-- internal signals --
							M00_AXIS_r, M00_AXIS_r_comb_out,
							-- AXI inptuts --
							M00_AXIS_ARESETN, M00_AXIS_TREADY
							)
	
		variable v									: M00_AXIS_inter;
		variable v_comb_out							: M00_AXIS_comb_out;
		variable r_local_address					: integer;
		
	begin
	
		-----------------------------------------------------------------
		--				   DEFAULT VARIABLES ASIGNATION		           --
		-----------------------------------------------------------------
		v 											:= M00_AXIS_r;	
		v.fifo_empty_vector							:= M00_AXIS_r.fifo_empty_vector;
		%(m00s_signals_variables)s
		-----------------------------------------------------------------
		--	 	DEFAULT COMBINATIONAL OUTPUT VARIABLES ASIGNATION      --
		-----------------------------------------------------------------
		v_comb_out									:= INIT_M00_AXIS_COMB_OUT;
		-----------------------------------------------------------------
		--	 			DEFAULT INTERNAL VARIABLE ASIGNATION      	   --
		-----------------------------------------------------------------
		r_local_address								:= to_integer(unsigned(M00_AXIS_r.current_tid));
		-----------------------------------------------------------------
		--	 					 AXIS MASTER CTRL FSM      	   		   --
		-----------------------------------------------------------------
		case M00_AXIS_r.axis_state is
			when idle =>
				if M00_AXIS_TREADY = '1' then			
					if v.fifo_empty_vector(to_integer(unsigned(M00_AXIS_r.current_tid))) = '1' then
						v.current_tid				:= std_logic_vector(unsigned(M00_AXIS_r.current_tid) + 1);
					else
						v.axis_state				:= runing;
					end if;
				end if;					
			when runing =>	
				case r_local_address is
                    %(m00s_signals_running)s
					when others => null;
				end case;
				if to_integer(unsigned(M00_AXIS_r.data_counter)) = S2MM_PACKET_SIZE-1 then
					v_comb_out.tlast				:= '1';
					v.current_tid					:= std_logic_vector(unsigned(M00_AXIS_r.current_tid) + 1);
					v.axis_state					:= idle;
				end if;	
			when others => null;
		end case;		
		---------------------------------------------------
		--				  RESET ASIGNATION		 	     --
		---------------------------------------------------		
		if M00_AXIS_ARESETN = '0' then
			v		    		:= INIT_M00_AXIS_INTER;
			v_comb_out			:= INIT_M00_AXIS_COMB_OUT;
		end if;
	
	---------------------------------------------------
	--				SIGNAL ASIGNATION			     --
	---------------------------------------------------
	M00_AXIS_rin 	       		<= v;
	M00_AXIS_rin_comb_out		<= v_comb_out;	
	
	end process;		
	
	---------------------------------------------------
	--		   INTERNAL ARCHITECTURE SIGNALS	 	 --
	---------------------------------------------------		
    %(m00s_signals_internal)s
    
	---------------------------------------------------
	--					 OUTPUTS			 	     --
	---------------------------------------------------			
	M00_AXIS_TVALID				<= M00_AXIS_rin_comb_out.tvalid;
	M00_AXIS_TDATA				<= M00_AXIS_rin_comb_out.tdata;
	M00_AXIS_TLAST				<= M00_AXIS_rin_comb_out.tlast;
	M00_AXIS_TID				<= M00_AXIS_r.current_tid;
	
end rtl;'''

makefile = r'''
SRCS=../ip/src/TASTE_AXI.vhd ../ip/src/%(pi)s
EXEC=./TASTE/TASTE.runs/impl_1/TASTE_wrapper.bit

all: ${EXEC}
    
${EXEC}: ${SRCS}
	vivado -mode batch -source TASTE_AXI.tcl

clean:
%(tab)srm -rf *.bit
'''

load_exec = r'''
#! /bin/bash

#Get the programming script path
TCL_DIR="$( cd "$( dirname "$0" )" >/dev/null 2>&1 && pwd )"
#Call the script 
/tools/Xilinx/Vivado/2019.2/bin/xsdb $TCL_DIR/programming.tcl $TCL_DIR $1
'''

programming_tcl = r'''
set host_ip 172.22.71.42
set host_port 3121

set path [lindex $argv 0]

cd $path

puts -nonewline "Connecting to ${host_ip}:${host_port}..."
connect -host 172.22.71.42 -port 3121
puts "OK!"
targets
targets 2
puts -nonewline "Reset the system..."
rst -system
puts "OK!"
puts "Load FPGA and configuring PS system"
fpga -f TASTE/TASTE.runs/impl_1/TASTE_wrapper.bit
source TASTE/TASTE.srcs/sources_1/bd/TASTE/ip/TASTE_processing_system7_0_0/ps7_init.tcl
ps7_init
ps7_post_config
puts "Load FPGA and configuring PS system OK!"
eval dow [lindex $argv 1]
con 
##Uncomment if it is deseired to run in two targets
##targets 3
##con -addr 0x00404040
puts "Software is running!"
'''


axi_support = r'''
#define ARM_CP15_TEXT_SECTION BSP_START_TEXT_SECTION

#include <bsp.h>
#include <bsp/start.h>
#include <bsp/arm-gic-irq.h>
#include <bsp/arm-cp15-start.h>
#include <bsp/arm-a9mpcore-start.h>


#ifdef ARMV7_CP15_START_DEFAULT_SECTIONS

BSP_START_DATA_SECTION static const arm_cp15_start_section_config zynq_mmu_config_table[] = {
    ARMV7_CP15_START_DEFAULT_SECTIONS,
    {
    .begin = 0xe0000000U,
    .end   = 0xe0200000U,
    .flags = ARMV7_MMU_DEVICE
    }, {
    .begin = 0xf8000000U,
    .end   = 0xf9000000U,
    .flags = ARMV7_MMU_DEVICE
    }, {
    .begin = 0x40000000U,
    .end   = 0xc0000000U,
    .flags = ARMV7_MMU_DEVICE
    }, {
    .begin = 0x00100000U,
    .end   = 0x00400000U,
    .flags = ARMV7_MMU_DEVICE
    }, {
    .begin = 0xfffc0000u,
    .end   = 0xffffffffu,
    .flags = ARMV7_MMU_DEVICE
    }
};

BSP_START_TEXT_SECTION void zynq_setup_mmu_and_cache(void) {
    uint32_t ctrl = arm_cp15_start_setup_mmu_and_cache(
    ARM_CP15_CTRL_A,
    ARM_CP15_CTRL_AFE | ARM_CP15_CTRL_Z
    );

    arm_cp15_start_setup_translation_table_and_enable_mmu_and_cache(
    ctrl,
    (uint32_t *) bsp_translation_table_base,
    ARM_MMU_DEFAULT_CLIENT_DOMAIN,
    &zynq_mmu_config_table[0],
    RTEMS_ARRAY_SIZE(zynq_mmu_config_table)
    );
}

#pragma message ("Memory configurations updated for AXI interfaces")

#endif
'''

per_circuit_vhd = """-- Company: GMV
-- Copyright European Space Agency, 2019-2020

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

%(declaration)s

architecture arch of %(pi)s_bambu is

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
      <spirit:name>S_AXIS</spirit:name>
      <spirit:busType spirit:vendor="xilinx.com" spirit:library="interface" spirit:name="axis" spirit:version="1.0"/>
      <spirit:abstractionType spirit:vendor="xilinx.com" spirit:library="interface" spirit:name="axis_rtl" spirit:version="1.0"/>
      <spirit:slave/>
      <spirit:portMaps>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>TDEST</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXIS_TDEST</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>TDATA</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXIS_TDATA</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>TLAST</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXIS_TLAST</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>TVALID</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXIS_TVALID</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>TREADY</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXIS_TREADY</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
      </spirit:portMaps>
    </spirit:busInterface>
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
      <spirit:name>S_AXIS_ACLK</spirit:name>
      <spirit:busType spirit:vendor="xilinx.com" spirit:library="signal" spirit:name="clock" spirit:version="1.0"/>
      <spirit:abstractionType spirit:vendor="xilinx.com" spirit:library="signal" spirit:name="clock_rtl" spirit:version="1.0"/>
      <spirit:slave/>
      <spirit:portMaps>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>CLK</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXIS_ACLK</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
      </spirit:portMaps>
      <spirit:parameters>
        <spirit:parameter>
          <spirit:name>ASSOCIATED_BUSIF</spirit:name>
          <spirit:value spirit:id="BUSIFPARAM_VALUE.S_AXIS_ACLK.ASSOCIATED_BUSIF">S_AXIS</spirit:value>
        </spirit:parameter>
        <spirit:parameter>
          <spirit:name>ASSOCIATED_RESET</spirit:name>
          <spirit:value spirit:id="BUSIFPARAM_VALUE.S_AXIS_ACLK.ASSOCIATED_RESET">S_AXIS_ARESETN</spirit:value>
        </spirit:parameter>
      </spirit:parameters>
    </spirit:busInterface>
    <spirit:busInterface>
      <spirit:name>S_AXIS_ACLK</spirit:name>
      <spirit:busType spirit:vendor="xilinx.com" spirit:library="signal" spirit:name="clock" spirit:version="1.0"/>
      <spirit:abstractionType spirit:vendor="xilinx.com" spirit:library="signal" spirit:name="clock_rtl" spirit:version="1.0"/>
      <spirit:slave/>
      <spirit:portMaps>
        <spirit:portMap>
          <spirit:logicalPort>
            <spirit:name>CLK</spirit:name>
          </spirit:logicalPort>
          <spirit:physicalPort>
            <spirit:name>S_AXIS_ACLK</spirit:name>
          </spirit:physicalPort>
        </spirit:portMap>
      </spirit:portMaps>
      <spirit:parameters>
        <spirit:parameter>
          <spirit:name>ASSOCIATED_BUSIF</spirit:name>
          <spirit:value spirit:id="BUSIFPARAM_VALUE.S_AXIS_ACLK.ASSOCIATED_BUSIF">S_AXIS</spirit:value>
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
      </spirit:parameters>
    </spirit:busInterface>
  </spirit:busInterfaces>
  <spirit:memoryMaps>
    <spirit:memoryMap>
      <spirit:name>S_AXI</spirit:name>
      <spirit:addressBlock>
        <spirit:name>reg0</spirit:name>
        <spirit:baseAddress spirit:format="bitString" spirit:resolve="user" spirit:bitStringLength="32">0</spirit:baseAddress>
        <spirit:range spirit:format="long" spirit:resolve="user" spirit:minimum="4096" spirit:rangeType="long">4294967296</spirit:range>
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
            <spirit:value>1800fe90</spirit:value>
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
            <spirit:value>1800fe90</spirit:value>
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
            <spirit:value>f92e9879</spirit:value>
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
    </spirit:ports>
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
        <spirit:name>src/TASTE_AXI.vhd</spirit:name>
        <spirit:fileType>vhdlSource</spirit:fileType>
        <spirit:userFileType>CHECKSUM_20a3fb2c</spirit:userFileType>
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
        <spirit:name>src/TASTE_AXI.vhd</spirit:name>
        <spirit:fileType>vhdlSource</spirit:fileType>
        <spirit:userFileType>IMPORTED_FILE</spirit:userFileType>
      </spirit:file>
    </spirit:fileSet>
    <spirit:fileSet>
      <spirit:name>xilinx_xpgui_view_fileset</spirit:name>
      <spirit:file>
        <spirit:name>xgui/TASTE_AXI_v1_0.tcl</spirit:name>
        <spirit:fileType>tclSource</spirit:fileType>
        <spirit:userFileType>CHECKSUM_f92e9879</spirit:userFileType>
        <spirit:userFileType>XGUI_VERSION_2</spirit:userFileType>
      </spirit:file>
    </spirit:fileSet>
  </spirit:fileSets>
  <spirit:description>TASTE_v1_0</spirit:description>
  <spirit:parameters>
    <spirit:parameter>
      <spirit:name>Component_Name</spirit:name>
      <spirit:value spirit:resolve="user" spirit:id="PARAM_VALUE.Component_Name" spirit:order="1">TASTE_v1_0</spirit:value>
    </spirit:parameter>
  </spirit:parameters>
  <spirit:vendorExtensions>
    <xilinx:coreExtensions>
      <xilinx:supportedFamilies>
        <xilinx:family xilinx:lifeCycle="Production">zynq</xilinx:family>
      </xilinx:supportedFamilies>
      <xilinx:taxonomies>
        <xilinx:taxonomy>/UserIP</xilinx:taxonomy>
      </xilinx:taxonomies>
      <xilinx:displayName>TASTE_v1_0</xilinx:displayName>
      <xilinx:definitionSource>package_project</xilinx:definitionSource>
      <xilinx:coreRevision>2</xilinx:coreRevision>
      <xilinx:coreCreationDateTime>2020-03-30T11:10:33Z</xilinx:coreCreationDateTime>
      <xilinx:tags>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@1caba8a6_ARCHIVE_LOCATION">/ip</xilinx:tag>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@54d0a6ec_ARCHIVE_LOCATION">/ip</xilinx:tag>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@3316f770_ARCHIVE_LOCATION">/ip</xilinx:tag>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@7b16f982_ARCHIVE_LOCATION">/ip</xilinx:tag>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@5717d5e9_ARCHIVE_LOCATION">/ip</xilinx:tag>
        <xilinx:tag xilinx:name="ui.data.coregen.dd@5a5ce90d_ARCHIVE_LOCATION">/ip</xilinx:tag>
      </xilinx:tags>
    </xilinx:coreExtensions>
    <xilinx:packagingInfo>
      <xilinx:xilinxVersion>2019.2</xilinx:xilinxVersion>
      <xilinx:checksum xilinx:scope="busInterfaces" xilinx:value="da618e65"/>
      <xilinx:checksum xilinx:scope="memoryMaps" xilinx:value="f2afdf52"/>
      <xilinx:checksum xilinx:scope="fileGroups" xilinx:value="7810a59c"/>
      <xilinx:checksum xilinx:scope="ports" xilinx:value="929b14a0"/>
      <xilinx:checksum xilinx:scope="parameters" xilinx:value="3fe0208c"/>
    </xilinx:packagingInfo>
  </spirit:vendorExtensions>
</spirit:component>"""
