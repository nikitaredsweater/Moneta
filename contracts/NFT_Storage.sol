// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title NFT_Storage
 * @dev ERC721-style NFT contract with mint, transfer, burn, and verify functionality
 */
contract NFT_Storage {
    // Token name
    string private _name;

    // Token symbol
    string private _symbol;

    // Mapping from token ID to owner address
    mapping(uint256 => address) private _owners;

    // Mapping owner address to token count
    mapping(address => uint256) private _balances;

    // Mapping from token ID to approved address
    mapping(uint256 => address) private _tokenApprovals;

    // Mapping from owner to operator approvals
    mapping(address => mapping(address => bool)) private _operatorApprovals;

    // Mapping from token hash to token ID
    mapping(bytes32 => uint256) private _hashToTokenId;

    // Mapping from token ID to token hash (reverse lookup)
    mapping(uint256 => bytes32) private _tokenIdToHash;

    // Mapping to check if a token hash exists
    mapping(bytes32 => bool) private _tokenHashExists;

    // Counter for token IDs
    uint256 private _tokenIdCounter;

    // Events
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);
    event Minted(address indexed to, uint256 indexed tokenId, bytes32 indexed tokenHash);
    event Burned(uint256 indexed tokenId, bytes32 indexed tokenHash);

    /**
     * @dev Initializes the contract by setting a `name` and a `symbol` to the token collection.
     */
    constructor(string memory name_, string memory symbol_) {
        _name = name_;
        _symbol = symbol_;
        _tokenIdCounter = 1; // Start token IDs from 1
    }

    /**
     * @dev Returns the token collection name.
     */
    function name() public view returns (string memory) {
        return _name;
    }

    /**
     * @dev Returns the token collection symbol.
     */
    function symbol() public view returns (string memory) {
        return _symbol;
    }

    /**
     * @dev Returns the number of tokens in `owner`'s account.
     */
    function balanceOf(address owner) public view returns (uint256) {
        require(owner != address(0), "ERC721: balance query for the zero address");
        return _balances[owner];
    }

    /**
     * @dev Returns the owner of the `tokenId` token.
     */
    function ownerOf(uint256 tokenId) public view returns (address) {
        address owner = _owners[tokenId];
        require(owner != address(0), "ERC721: owner query for nonexistent token");
        return owner;
    }

    /**
     * @dev Safely mints a new NFT with a unique hash
     * @param to The address that will own the minted NFT
     * @param tokenHash The unique hash representing the NFT data
     * @return tokenId The ID of the newly minted token
     */
    function mintNFT(address to, bytes32 tokenHash) public returns (uint256) {
        require(to != address(0), "ERC721: mint to the zero address");
        require(!_tokenHashExists[tokenHash], "NFT_Storage: token hash already exists");

        uint256 tokenId = _tokenIdCounter;
        _tokenIdCounter++;

        _balances[to] += 1;
        _owners[tokenId] = to;
        _hashToTokenId[tokenHash] = tokenId;
        _tokenIdToHash[tokenId] = tokenHash;
        _tokenHashExists[tokenHash] = true;

        emit Transfer(address(0), to, tokenId);
        emit Minted(to, tokenId, tokenHash);

        return tokenId;
    }

    /**
     * @dev Transfers `tokenId` token from `from` to `to`.
     */
    function transferNFT(address from, address to, uint256 tokenId) public {
        require(_isApprovedOrOwner(msg.sender, tokenId), "ERC721: transfer caller is not owner nor approved");
        require(ownerOf(tokenId) == from, "ERC721: transfer from incorrect owner");
        require(to != address(0), "ERC721: transfer to the zero address");

        // Clear approvals from the previous owner
        _approve(address(0), tokenId);

        _balances[from] -= 1;
        _balances[to] += 1;
        _owners[tokenId] = to;

        emit Transfer(from, to, tokenId);
    }

    /**
     * @dev Safely transfers `tokenId` token from `from` to `to` (alias for ERC721 compatibility)
     */
    function safeTransferFrom(address from, address to, uint256 tokenId) public {
        transferNFT(from, to, tokenId);
    }

    /**
     * @dev Transfers `tokenId` token from `from` to `to` (alias for ERC721 compatibility)
     */
    function transferFrom(address from, address to, uint256 tokenId) public {
        transferNFT(from, to, tokenId);
    }

    /**
     * @dev Burns (destroys) the NFT with the given tokenId
     * @param tokenId The ID of the token to burn
     */
    function burnNFT(uint256 tokenId) public {
        require(_isApprovedOrOwner(msg.sender, tokenId), "ERC721: burn caller is not owner nor approved");

        address owner = ownerOf(tokenId);

        // Find and remove the token hash
        bytes32 tokenHash = _findTokenHash(tokenId);
        if (tokenHash != bytes32(0)) {
            _tokenHashExists[tokenHash] = false;
            delete _hashToTokenId[tokenHash];
            delete _tokenIdToHash[tokenId];
        }

        // Clear approvals
        _approve(address(0), tokenId);

        _balances[owner] -= 1;
        delete _owners[tokenId];

        emit Transfer(owner, address(0), tokenId);
        emit Burned(tokenId, tokenHash);
    }

    /**
     * @dev Verifies if an NFT with the given hash exists
     * @param tokenHash The hash to verify
     * @return bool True if the token exists, false otherwise
     */
    function verifyNFT(bytes32 tokenHash) public view returns (bool) {
        return _tokenHashExists[tokenHash];
    }

    /**
     * @dev Returns the token ID associated with a given hash
     * @param tokenHash The hash to look up
     * @return tokenId The token ID (returns 0 if not found)
     */
    function getTokenIdByHash(bytes32 tokenHash) public view returns (uint256) {
        require(_tokenHashExists[tokenHash], "NFT_Storage: token hash does not exist");
        return _hashToTokenId[tokenHash];
    }

    /**
     * @dev Approve `to` to operate on `tokenId`
     */
    function approve(address to, uint256 tokenId) public {
        address owner = ownerOf(tokenId);
        require(to != owner, "ERC721: approval to current owner");
        require(msg.sender == owner || isApprovedForAll(owner, msg.sender),
                "ERC721: approve caller is not owner nor approved for all");

        _approve(to, tokenId);
    }

    /**
     * @dev Returns the account approved for `tokenId` token.
     */
    function getApproved(uint256 tokenId) public view returns (address) {
        require(_exists(tokenId), "ERC721: approved query for nonexistent token");
        return _tokenApprovals[tokenId];
    }

    /**
     * @dev Approve or remove `operator` as an operator for the caller.
     */
    function setApprovalForAll(address operator, bool approved) public {
        require(operator != msg.sender, "ERC721: approve to caller");
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }

    /**
     * @dev Returns if the `operator` is allowed to manage all of the assets of `owner`.
     */
    function isApprovedForAll(address owner, address operator) public view returns (bool) {
        return _operatorApprovals[owner][operator];
    }

    /**
     * @dev Returns whether `tokenId` exists.
     */
    function _exists(uint256 tokenId) internal view returns (bool) {
        return _owners[tokenId] != address(0);
    }

    /**
     * @dev Returns whether `spender` is allowed to manage `tokenId`.
     */
    function _isApprovedOrOwner(address spender, uint256 tokenId) internal view returns (bool) {
        require(_exists(tokenId), "ERC721: operator query for nonexistent token");
        address owner = ownerOf(tokenId);
        return (spender == owner || getApproved(tokenId) == spender || isApprovedForAll(owner, spender));
    }

    /**
     * @dev Approve `to` to operate on `tokenId`
     */
    function _approve(address to, uint256 tokenId) internal {
        _tokenApprovals[tokenId] = to;
        emit Approval(ownerOf(tokenId), to, tokenId);
    }

    /**
     * @dev Helper function to find token hash by token ID (reverse lookup)
     */
    function _findTokenHash(uint256 tokenId) internal view returns (bytes32) {
        return _tokenIdToHash[tokenId];
    }

    /**
     * @dev Public function to get the hash of a token by its ID
     * @param tokenId The token ID to look up
     * @return tokenHash The hash associated with the token
     */
    function getTokenHash(uint256 tokenId) public view returns (bytes32) {
        require(_exists(tokenId), "NFT_Storage: token does not exist");
        return _tokenIdToHash[tokenId];
    }
}
