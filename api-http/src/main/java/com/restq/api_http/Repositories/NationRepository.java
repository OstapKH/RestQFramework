package com.restq.api_http.Repositories;

import com.restq.api_http.DTO.VolumeShippingOfNations;
import com.restq.core.Models.Nation.Nation;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.sql.Date;
import java.util.List;


public interface NationRepository extends JpaRepository<Nation, Long> {

    @Query("""
            SELECT new com.restq.api_http.DTO.VolumeShippingOfNations(\
            n1.name, n2.name, EXTRACT(YEAR FROM l.shipDate), SUM(l.extendedPrice * (1 - l.discount))) \
            FROM Supplier s, LineItem l, Order o, Customer c, Nation n1, Nation n2 \
            WHERE s.supplierKey = l.suppKey \
            AND o.orderKey = l.orderKey \
            AND c.customerKey = o.customer.customerKey \
            AND s.nation.nationKey = n1.nationKey \
            AND c.nation.nationKey = n2.nationKey \
            AND ((n1.name = :nation1 AND n2.name = :nation2) OR (n1.name = :nation2 AND n2.name = :nation1)) \
            AND l.shipDate BETWEEN :startDate AND :endDate \
            GROUP BY n1.name, n2.name, EXTRACT(YEAR FROM l.shipDate) \
            ORDER BY n1.name, n2.name, EXTRACT(YEAR FROM l.shipDate)""")
        // Q7
    List<VolumeShippingOfNations> getNationsVolumeShipping(@Param("nation1") String nation1, @Param("nation2") String nation2, @Param("startDate") Date startDate, @Param("endDate") Date endDate);
}
