------------------------------------------------------------------------------------------
-- Title : Routing control for a crossbar switch.
----------------------------------------------------------------------------
-- Description: Controller for routing a packet to one of two outputs depending on the zeroth bit of the packet header word
--		       The whole packet is then sent out, stopping when the 'FF' word is sensed. 
--  		       The controller sends request signals to the appropriate output and sends the message on when it gets a grant signal in return.
-----------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity control is
		PORT(
    enable : OUT std_logic;
    reqx : OUT std_logic;
    reqy : OUT std_logic;
    write : OUT std_logic;
    available : IN std_logic;
    clk : IN std_logic;
    data_in : IN std_logic_vector(7 DOWNTO 0);
    gntx : IN std_logic;
    gnty : IN std_logic;
    reset : IN std_logic
);
end control;
architecture behavior of control is
-- Behaviour follows the 'classic' state machine method
    -- Possible states.

    type states is (poll_fifo, raise_enable, check_data, setup_x, setup_y, data_xfer, data_yfer);

    -- Present state.

    signal present_state : states;

begin

    -- Main process.

    process (clk, reset)

    begin

        -- Activities triggered by asynchronous reset (active low).

        if (reset = '0') then

            -- Set the default state and outputs.

            present_state <= poll_fifo;
            

        elsif (clk'event and clk = '1') then

            -- Set the default state and outputs.

--            present_state <= poll_fifo;
            enable <= '0';
            reqx <= '0';
            reqy <= '0';
            write <= '0';

            case present_state is

                when poll_fifo =>
                	if (available = '1') then
                        present_state <= raise_enable;
                    end if;
		
                when raise_enable =>
                    enable <= '1';
			        present_state <= check_data;
 
                when check_data =>
                    if (data_in(0)='0') then
                        present_state <= setup_x;
			        else
			            present_state <= setup_y;
			        end if;

                when setup_x =>
			       -- reqx <= '1';
			        present_state <= data_xfer;

                when setup_y =>
                    reqy <= '1';
                    present_state <= data_yfer;

                when data_xfer =>
                    reqx <= '1';
                    if(gntx = '1') then
                        present_state <= poll_fifo;
                    end if;

                when data_yfer =>
                    if(gnty = '1') then
                        present_state <= poll_fifo;
                    end if;
			
                when others =>
                    present_state <= poll_fifo;
                    enable <= '0';
                    reqx <= '0';
                    reqy <= '0';
                    write <= '0';
            		
            end case;
        end if;
    end process;
end behavior;
