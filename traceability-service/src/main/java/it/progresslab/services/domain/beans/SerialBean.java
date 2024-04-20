package it.progresslab.services.domain.beans;

import it.progresslab.services.avro.Serial;

import java.util.Objects;

/**
 * Simple DTO used by the REST interface
 */
public class SerialBean {

    private String id;
    private String serialId;
    private int quantity;

    public SerialBean() {

    }

    public SerialBean(final String id, final String serialId, final int quantity) {
        this.id = id;
        this.serialId = serialId;
        this.quantity = quantity;
    }

    public static SerialBean toBean(final Serial serial) {
        return new SerialBean(serial.getId(),
                serial.getSerialId(),
                serial.getQuantity());
    }

    public static Serial fromBean(final SerialBean order) {
        return new Serial(order.getId(),
                order.getSerialId(),
                order.getQuantity());
    }

    public String getId() {
        return id;
    }

    public String getSerialId() {
        return serialId;
    }

    public int getQuantity() {
        return quantity;
    }

    @Override
    public boolean equals(final Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || this.getClass() != o.getClass()) {
            return false;
        }

        final SerialBean serialBean = (SerialBean) o;

        if (this.quantity != serialBean.quantity) {
            return false;
        }
        return Objects.equals(this.id, serialBean.id) && Objects.equals(this.serialId, serialBean.serialId);
    }

    @Override
    public String toString() {
        return "SerialBean{id='%s', serialId=%s, quantity=%d}".formatted(id, serialId, quantity);
    }

    @Override
    public int hashCode() {
        int result;
        final long temp;
        result = this.id != null ? this.id.hashCode() : 0;
        result = 31 * result + (this.serialId != null ? this.serialId.hashCode() : 0);
        result = 31 * result + this.quantity;
        return result;
    }

}
