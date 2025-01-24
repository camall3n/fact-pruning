(define (problem minecraft-multi-object-01-04)

    (:domain minecraft-multi-object)

    (:objects
        ag01 - agent
        n00 n01 n02 n03 n04 - int
    )

    (:init
        ; ----- inventory -----
        (hungry ag01)
        (has-logs ag01 n00)
        (has-sticks ag01 n00)
        (has-iron ag01 n00)
        (has-wool ag01 n00)
        ; ----- misc -----
        (are-seq n00 n01)
        (are-seq n01 n02)
        (are-seq n02 n03)
        (are-seq n03 n04)
        (= (total-cost) 0)
    )

(:goal (and (tribe-has-food)))

(:metric minimize (total-cost))

)
