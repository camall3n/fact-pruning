(define (problem minecraft-cyclic-02-03)

    (:domain minecraft-cyclic)

    (:objects
        ag01 ag02 - agent
        n00 n01 n02 n03 - int
    )

    (:init
        ; ----- inventory -----
        (hungry ag01)
        (hungry ag02)
        (has-logs ag01 n00)
        (has-logs ag02 n00)
        (has-sticks ag01 n00)
        (has-sticks ag02 n00)
        (has-iron ag01 n00)
        (has-iron ag02 n00)
        (has-wool ag01 n00)
        (has-wool ag02 n00)
        (has-food ag01 n00)
        (has-food ag02 n00)
        ; ----- misc -----
        (are-seq n00 n01)
        (are-seq n01 n02)
        (are-seq n02 n03)
        (= (total-cost) 0)
    )

(:goal (and (tribe-has-food)))

(:metric minimize (total-cost))

)
