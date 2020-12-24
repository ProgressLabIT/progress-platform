get_product_bom = """
  FOR v,e,p IN 1..2 OUTBOUND 'Product/11728033' requires

    FILTER v._id like 'ProductionItem/%'
    
    /*  check if last edge to ProductionItem started from Phase or directly from Product
        if yes, get the phase sequence from the ProductPhase relationship, which
        is the first of the two edges of the path.
        
        (this might be simplified storing the sequence on the Phase document
        rather than in its relationship to the product)
    */
    LET phase_seq = e._from like 'Phase/%' ? p.edges[0].sequence : null 
    
    RETURN {
        _key: v._key,
        code: v.code,
        description: v.description,
        type: v.type,
        phase_seq: phase_seq,
        // get operation name
        operation: (FOR op, r in 1..1 OUTBOUND DOCUMENT(e._from) requires FILTER r.type == 'PhaseOperation' RETURN op.description)[0]
        // missing the required quantity: not stored in the test data
    }
        
"""