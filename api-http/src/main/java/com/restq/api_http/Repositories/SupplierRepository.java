package com.restq.api_http.Repositories;

import com.restq.api_http.DTO.LocalSupplierVolume;
import com.restq.core.Models.Supplier.Supplier;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDate;
import java.util.List;

public interface SupplierRepository extends JpaRepository<Supplier, Long> {
    @Query("""
            SELECT new com.restq.api_http.DTO.LocalSupplierVolume(\
           n.name, SUM(l.extendedPrice * (1 - l.discount))) \
            FROM Customer c, Order o, LineItem l, Supplier s, Nation n, Region r \
            WHERE c.customerKey = o.customer.customerKey \
            AND l.orderKey = o.orderKey \
            AND l.suppKey = s.supplierKey \
            AND c.nation.nationKey = s.nation.nationKey \
            AND s.nation.nationKey = n.nationKey \
            AND n.region.regionKey = r.regionKey \
            AND r.name = :region \
            AND o.orderDate >= :startDate \
            AND o.orderDate < :endDate \
            GROUP BY n.name \
            ORDER BY SUM(l.extendedPrice * (1 - l.discount)) DESC \
            """)
    // Q5
    List<LocalSupplierVolume> findLocalSupplierVolume(
            @Param("region") String region,
            @Param("startDate") LocalDate startDate,
            @Param("endDate") LocalDate endDate);
}
