// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Vault {
    mapping(address => uint256) public balances;

    // Anyone can deposit Ether into the Vault
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    // Vulnerable withdraw function (Reentrancy + no access control)
    function withdraw(uint256 _amount) external {
        require(balances[msg.sender] >= _amount, "Insufficient balance");

        // Interaction before state change → Reentrancy bug
        (bool sent, ) = msg.sender.call{value: _amount}("");
        require(sent, "Failed to send Ether");

        // Update balance after transfer (bad order)
        balances[msg.sender] -= _amount;
    }

    // No fallback/receive protection
    receive() external payable {}
}
