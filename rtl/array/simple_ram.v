// Provide 4 KiB RAM with byte writes and optional firmware loading.

module simple_ram #(
    parameter INIT_FILE = ""
) (
    input wire clk,
    input wire reset,
    input wire mem_valid,
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    input wire [3:0] mem_wstrb,
    output wire mem_ready,
    output wire [31:0] mem_rdata
);
    
    reg [31:0] memory [0:1023];
    wire selected;
    wire [9:0] word_index;

    initial begin
        if (INIT_FILE != "")
            $readmemh(INIT_FILE, memory);
    end

    assign selected = (mem_addr[31:12] == 20'h00000);
    // Convert byte address to word index.
    assign word_index = mem_addr[11:2];

    assign mem_ready = mem_valid && selected && !reset;
    assign mem_rdata = selected ? memory[word_index] : 32'b0;

    // Update enabled bytes only.
    always @(posedge clk) begin
        if (mem_valid && mem_ready) begin
            if (mem_wstrb[0])
                memory[word_index][7:0] <= mem_wdata[7:0];
            if (mem_wstrb[1])
                memory[word_index][15:8] <= mem_wdata[15:8];
            if (mem_wstrb[2])
                memory[word_index][23:16] <= mem_wdata[23:16];
            if (mem_wstrb[3])
                memory[word_index][31:24] <= mem_wdata[31:24];
        end
    end

endmodule
