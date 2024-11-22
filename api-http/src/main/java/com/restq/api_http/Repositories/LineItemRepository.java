package com.restq.api_http.Repositories;

import com.restq.api_http.DTO.PricingSummaryReport;
import com.restq.core.Models.LineItem.LineItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.sql.Date;
import java.util.List;


@Repository
public interface LineItemRepository extends JpaRepository<LineItem, Long> {

    @Query("""
            SELECT new com.restq.api_http.DTO.PricingSummaryReport(\
            l.returnFlag, l.lineStatus, \
            SUM(l.quantity), SUM(l.extendedPrice), \
            SUM(l.extendedPrice * (1 - l.discount)), \
            SUM(l.extendedPrice * (1 - l.discount) * (1 + l.tax)), \
            AVG(l.quantity), AVG(l.extendedPrice), \
            AVG(l.discount), COUNT(l) \
            ) FROM LineItem l \
            WHERE l.shipDate <= :shipDate \
            GROUP BY l.returnFlag, l.lineStatus \
            ORDER BY l.returnFlag, l.lineStatus""")
    // Q1
    List<PricingSummaryReport> getPricingSummaryReport(@Param("shipDate") Date shipDate);


    @Query("""
            SELECT SUM(l.extendedPrice * l.discount) AS revenue \
            FROM LineItem l \
            WHERE l.shipDate >= :startDate \
              AND l.shipDate < :endDate \
              AND l.discount BETWEEN :discount - 0.01 AND :discount + 0.01 \
              AND l.quantity < :quantity \
            """)
    // Q6
    BigDecimal calculateRevenueIncrease(
            @Param("startDate") Date startDate,
            @Param("endDate") Date endDate,
            @Param("discount") Double discount,
            @Param("quantity") Integer quantity
    );
}