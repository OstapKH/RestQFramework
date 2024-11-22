package com.restq.api_http.Repositories;

import com.restq.api_http.DTO.SupplierPartInfo;
import com.restq.core.Models.Part.Part;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PartRepository extends JpaRepository<Part, Long> {
    @Query("""
            SELECT new com.restq.api_http.DTO.SupplierPartInfo(\
            s.accountBalance, s.name, n.name, p.partKey, p.manufacturer, s.address, s.phone, s.comment) \
            FROM Part p, Supplier s, PartSupp ps, Nation n, Region r \
            WHERE p.partKey = ps.part.partKey \
            AND ps.supplier.supplierKey = s.supplierKey \
            AND p.size = :size \
            AND p.type LIKE %:type \
            AND s.nation.nationKey = n.nationKey \
            AND n.region.regionKey = r.regionKey \
            AND r.name = :region \
            AND ps.supplyCost = ( \
                SELECT MIN(ps2.supplyCost) \
                FROM PartSupp ps2, Supplier s2, Nation n2, Region r2 \
                WHERE ps2.part.partKey = p.partKey \
                AND ps2.supplier.supplierKey = s2.supplierKey \
                AND s2.nation.nationKey = n2.nationKey \
                AND n2.region.regionKey = r2.regionKey \
                AND r2.name = :region \
            ) \
            ORDER BY s.accountBalance DESC, n.name, s.name, p.partKey""")
    // Q2
    List<SupplierPartInfo> findSupplierPartInfo(@Param("size") Integer size, @Param("type") String type, @Param("region") String region);
}