contract Case3 {
    mapping(address => uint256) public lastClaim;

    function claim() public {
        require(block.timestamp - lastClaim[msg.sender] >= 86400, "Wait a day");
        lastClaim[msg.sender] = block.timestamp;
        // give reward
    }
}